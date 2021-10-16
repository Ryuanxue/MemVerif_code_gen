#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Function.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/IR/User.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Instruction.h>
#include <llvm/IR/InstIterator.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Metadata.h>
#include <llvm/IR/DebugInfo.h>
#include <llvm/IR/DebugLoc.h>
#include <llvm/IR/IntrinsicInst.h>
#include <llvm/Pass.h>
#include <fstream>
#include <string>
#include "llvm/IR/DebugInfoMetadata.h"
#include <llvm/Analysis/CFG.h>
#include <stdio.h>
#include <map>
#include "llvm/Support/Casting.h"
using namespace llvm;
using namespace std;



namespace {
	struct CFGPass : public FunctionPass {
		static char ID;
		std::error_code error;
		std::string str;
		//StringMap<int> basicblockMap;
		std::map<BasicBlock*, int> basicBlockMap;
		int bbCount;  //Block的编号
		CFGPass() : FunctionPass(ID){
			bbCount = 0;
		}


		bool isllvm(CallInst *inst){ //此函数判断函数调用指令是否包含llvm，输出的cfg信息中应该去除这些信息
			std::string name;
			Function* called = inst->getCalledFunction();
			if(called){
				name=called->getName().str();

				}
			if(name.compare(0,4,"llvm")==0){
				return 1;
				}else{
					return 0;
				}
		}
		

		bool runOnFunction(Function &F) override{
			raw_string_ostream rso(str);
			std::string name= F.getName().str() + ".dot";
			
			enum sys::fs::OpenFlags F_None;
			raw_fd_ostream file(name, error, F_None);
			//std::ofstream os;
			//os.open(name.str() + ".dot");
			//if (!os.is_open()){
			//	errs() << "Could not open the " << name << "file\n";
			//	return false;
			//}
			file << "digraph \"CFG for'" + F.getName() + "\' function\" {\n";
			file<<"\tBB"<<F.getName().str()<<"_start"<<"[shape=record,label=\"{";
			file<<F.getName().str()<<"_start";
			file << "}\"];\n";
			file << "\tBB" << F.getName().str()<<"_start"<<"-> "<<F.getName().str()<<"BB"
						<< bbCount << ";\n";
			int fromCountNum;
			int toCountNum;
			for (Function::iterator B_iter = F.begin(); B_iter != F.end(); ++B_iter){
				
				BasicBlock* curBB = &*B_iter;
				std::string name = curBB->getName().str();
				
				if (basicBlockMap.find(curBB) != basicBlockMap.end())
				{
					fromCountNum = basicBlockMap[curBB];
				}
				else
				{
					fromCountNum = bbCount;
					basicBlockMap[curBB] = bbCount++;
				}
				

				file <<"\t"<<F.getName().str()<<"BB" << fromCountNum << " [shape=record, label=\"{";
				file << "BB" << fromCountNum << ":\\l\\l";
				Instruction *pre=&*(curBB->begin());
				int funnum=0;
				for (BasicBlock::iterator I_iter = curBB->begin(); I_iter != curBB->end(); ++I_iter) 
				{
					
					Instruction *I = &*I_iter;
					
					unsigned Line;

                  	StringRef File;
                  	StringRef Dir;

					if (DILocation *Loc = I->getDebugLoc())
					{
                  		Line = Loc->getLine();
                  		File = Loc->getFilename();
                  		Dir = Loc->getDirectory();
                  						
          			}


					if (I==&*(curBB->begin()))
					{
						CallInst *inst = dyn_cast<CallInst>(I);

						if (inst&&!isllvm(inst))

						{
							funnum++;								
                  			file << Dir << "/" << File << ":" << Line << "\\l\n";                			
          			  		file << *I_iter << "\\l\n";
          			  		file << "}\"];\n";						
							pre=&*I_iter;
						}else
						{
							file << Dir << "/" << File << ":" << Line << "\\l\n";               
          			  		file << *I_iter << "\\l\n";
          			  		pre=&*I_iter;         			  		
						}

					}else
					{
						CallInst *inst = dyn_cast<CallInst>(pre);

						if (inst&&!isllvm(inst))
						{
							int tempNum;
							
							if(funnum==1||funnum==0)
							{
								tempNum=basicBlockMap[curBB];

							}
							else
							{
								tempNum=bbCount-1;
							}
							file << "\t"<<F.getName().str()<<"BB" << tempNum<< "-> "<<F.getName().str()<<"BB"
							<< bbCount << ";\n";
							file << "\t"<<F.getName().str()<<"BB" << bbCount << " [shape=record, label=\"{";
							file << "BB" << bbCount << ":\\l\\l";
							fromCountNum=bbCount;
							bbCount++;
							CallInst *inst = dyn_cast<CallInst>(I);

							if (inst&&!isllvm(inst))

							{
								funnum++;
              					file << Dir << "/" << File << ":" << Line << "\\l\n";;
      			  				file << *I_iter << "\\l\n";
      			  				file << "}\"];\n";
      			  				pre=&*I_iter;

							}else
							{
								file << Dir << "/" << File << ":" << Line << "\\l\n";;               
          			  			file << *I_iter << "\\l\n";
          			  			pre=&*I_iter;
							}	
						}else
						{
							CallInst *inst = dyn_cast<CallInst>(I);

							if (inst&&!isllvm(inst))
							{
								funnum++;										
              					file << Dir << "/" << File << ":" << Line << "\\l\n";;
      			  				file << *I_iter << "\\l\n";
      			  				file << "}\"];\n";
								pre=&*I_iter;
							}else
							{
								file << Dir << "/" << File << ":" << Line << "\\l\n";;	                
	          			  		file << *I_iter << "\\l\n";
	          			  		pre=&*I_iter;
							}
						}
					}
					
				}
				file << "}\"];\n";
				for (BasicBlock *SuccBB : successors(curBB))
				{
					if (basicBlockMap.find(SuccBB) != basicBlockMap.end())
					{
						toCountNum = basicBlockMap[SuccBB];
					}
					else
					{
						toCountNum = bbCount;
						basicBlockMap[SuccBB] = bbCount++;
					}

					file << "\t"<<F.getName().str()<<"BB" << fromCountNum<< "-> "<<F.getName().str()<<"BB"
						<< toCountNum << ";\n";
				}
			}
			int num=bbCount-1;

			// file << "\t"<<F.getName().str()<<"BB" << num<<"-> BB"<<
			// 			F.getName().str()<<"_end"<< ";\n";

			// file<<"\tBB"<<F.getName().str()<<"_end"<<"[shape=record,label=\"{";
			// 	file<<F.getName().str()<<"_end";
			// 	file << "}\"];\n";
			file << "}\n";
							
			file.close();
			return true;
		}

	};
}

char CFGPass::ID = 0;
static RegisterPass<CFGPass> X("CFG", "CFG Pass Analyse",
	false, false);
