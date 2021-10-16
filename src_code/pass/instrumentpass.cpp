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
#include <llvm/IR/LLVMContext.h>
#include "../IR/LLVMContextImpl.h"
#include <fstream>
#include <string>
#include "llvm/IR/DebugInfoMetadata.h"
#include "llvm/IR/IRBuilder.h"
#include <llvm/Analysis/CFG.h>
#include <stdio.h>
 #include<set>
#include <map>
#include <iostream>
#include "tinyxml2.h"
#include <algorithm>
 
using namespace tinyxml2;

#include "llvm/Support/Casting.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
using namespace llvm;
using namespace std;

static cl::opt<std::string> getxmlfilename("xml-filename", cl::desc("Specify xml filename for mypass"), cl::value_desc("xml-filename"));
// static cl::opt<std::string> getlinenum("line-num", cl::desc("Specify insert line number for mypass"), cl::value_desc("linenumber"));
// static cl::opt<std::string> getovertype("over-type", cl::desc("Specify overread type  for mypass"), cl::value_desc("overtype"));
// static cl::opt<std::string> getbound("bound", cl::desc("Specify overread bound  for mypass"), cl::value_desc("bound"));

map<string,vector<string> > functionmap;


namespace 
{
	struct PProcessPass : public ModulePass 
	{
		static char ID;
		std::string str;
		FILE *fstream;
        Value *pFile;
        StructType* IO_FILE_ty;
        Type *IO_FILE_PTR_ty;
        Value *FPrintf;
        CallInst* ptr_call;


	
		PProcessPass() : ModulePass(ID)
		{
		}

		virtual Instruction* insertOnMainEntryBlock(BasicBlock &F, Module &M,Instruction *in) 
        {
            // Returns a pointer to the first instruction in this block
            // that is not a PHINode instruction
            Instruction *inst = in;


                // FILE * pFile;
                
                StructType* IO_marker_ty = StructType::create(M.getContext(), "struct._IO_marker");
                PointerType* IO_marker_ptr_ty = PointerType::getUnqual(IO_marker_ty);

                std::vector<Type*> Elements;
                Elements.push_back(IO_marker_ptr_ty);
                Elements.push_back(IO_FILE_PTR_ty);
                IO_FILE_ty->setBody(Elements, false);

                std::vector<Type*> Elements2;
                Elements2.push_back(IO_marker_ptr_ty);
                Elements2.push_back(IO_FILE_PTR_ty);
                Elements2.push_back(Type::getInt32Ty(M.getContext()));;
                IO_marker_ty->setBody(Elements2, false);

                



                // FILE * fopen ( const char * , const char *  );
                std::vector<Type*> Params;
                Params.push_back(PointerType::getUnqual(Type::getInt8PtrTy(F.getContext())));
                Params.push_back(PointerType::getUnqual(Type::getInt8PtrTy(F.getContext())));

                
                FunctionCallee funcall1= M.getOrInsertFunction("fopen",
                                                            IO_FILE_PTR_ty,
                                                            Type::getInt8PtrTy(F.getContext()),
                                                            Type::getInt8PtrTy(F.getContext())
                                                            //Params
                                                            );


                Value* const_fopen =funcall1.getCallee();
                Function *func_fopen = dyn_cast<Function>(const_fopen);

                // //Create a global string variable with the file's name
                Constant* strfileConstant = ConstantDataArray::getString(
                                                                M.getContext(),
                                                                "test.txt",
                                                                true);

                GlobalVariable* fileStr = new GlobalVariable(M,
                                                    strfileConstant->getType(),
                                                    true,
                                                    llvm::GlobalValue::InternalLinkage , 
                                                    strfileConstant,
                                                    "testTxt");


                //Get the int8ptr to our message
                Constant* constZeroF = ConstantInt::get(Type::getInt32Ty(M.getContext()), 0);
                Constant* constArrayF = ConstantExpr::getInBoundsGetElementPtr(strfileConstant->getType(),fileStr, constZeroF);
                Value* filePtr = ConstantExpr::getBitCast(constArrayF, PointerType::getUnqual(Type::getInt8Ty(M.getContext())));

                // //Create a global strin g variable with the format's name
                Constant* strFormatConstant = ConstantDataArray::getString( M.getContext(),
                                                                            "a+",
                                                                            true);

                GlobalVariable* formatStr = new GlobalVariable(M,
                                                strFormatConstant->getType(),
                                                true,
                                                llvm::GlobalValue::InternalLinkage,
                                                strFormatConstant,
                                                "a+");

                // // Get the int8ptr to our message
                Constant* constZeroFmt  = ConstantInt::get(Type::getInt32Ty(M.getContext()), 0);
                Constant* constArrayFmt = ConstantExpr::getInBoundsGetElementPtr(strFormatConstant->getType(),formatStr, constZeroFmt);
                Value* fmtPtr = ConstantExpr::getBitCast(constArrayFmt, PointerType::getUnqual(Type::getInt8Ty(M.getContext())));

                vector<Value*> args;
                args.push_back(filePtr);
                args.push_back(fmtPtr);
                IRBuilder<> ThenB(in);
                Instruction *allcapfile =ThenB.CreateAlloca(IO_FILE_PTR_ty,nullptr,"pFile");
                Instruction *fopen= ThenB.CreateCall(func_fopen, args, "fopen");
                ThenB.CreateStore(fopen,allcapfile);
                //insertprintf(in,M,incval,allcapfile);

                //pFile = CallInst::Create(func_fopen, args, "", inst->getNextNode());
            
            return allcapfile;
            // return in;
        }

        virtual bool insertOnMainEndBlock(BasicBlock &F,Instruction *in, Module &M,Instruction *pfile) {
            Instruction *inst = in;

            // int fclose(FILE*);
            
            FunctionCallee funcall2= M.getOrInsertFunction("fclose",
                                                Type::getInt32Ty(F.getContext()),
                                                        IO_FILE_PTR_ty);
            Value* const_fclose =funcall2.getCallee();

            Function *func_fclose = cast<Function>(const_fclose);
            IRBuilder<> ThenB(in);
            Value* next = ThenB.CreateLoad(pfile);
            vector<Value*> args;
            args.push_back(next);


            
                ThenB.CreateCall(func_fclose, next);

            // CallInst* int32_call3 = CallInst::Create(func_fclose,
            //                                         pFile,
            //                                         "",
            //                                         inst);

            // int32_call3->setCallingConv(CallingConv::C);
            // int32_call3->setTailCall(true);

            return true;
        }

        virtual Value* getstrlen(BasicBlock &F,Module &M,Instruction *in,Value *arg)
        {
            PointerType *Pty = PointerType::get(IntegerType::get(F.getContext(), 8), 0);
            FunctionCallee callstrlen=M.getOrInsertFunction("strlen",Type::getInt64Ty(F.getContext()),Pty);

            Value* const_strlen=callstrlen.getCallee();

            Function *func_strlen = cast<Function>(const_strlen);

            IRBuilder<> ThenB(in);
            Value *len_str=ThenB.CreateAlloca(Type::getInt64Ty(F.getContext()));
            
            Instruction *ins_strlen= ThenB.CreateCall(func_strlen, arg);
            Instruction *storelen=ThenB.CreateStore(ins_strlen,len_str);
            Value *len_load=ThenB.CreateLoad(len_str);
            return len_load;


        }

        virtual Function* getfprint(Module &mod, LLVMContext& ctx , vector<Value*> args) {
            vector<Type*> argsTypes;

            // push type of FILE*
            argsTypes.push_back(IO_FILE_PTR_ty);
            // push rest arguments of printf instruction
            for (unsigned i = 1, e = args.size(); i != e; i++) {
                argsTypes.push_back(args[i]->getType());
            }

            // create fprintf function
            FunctionCallee funcall = mod.getOrInsertFunction("fprintf",
                                        FunctionType::get(Type::getInt32Ty(ctx),
                                                        argsTypes,
                                                        true));
            FPrintf=funcall.getCallee ();

            Function *func_fprintf = dyn_cast<Function>(FPrintf);
            func_fprintf->setCallingConv(CallingConv::C);

            return func_fprintf;
        }

        virtual bool insertprintf(Instruction *I, Module &M,Value *val, Instruction *pfile,string File,unsigned Line,Value *arg2_int) {
            LLVMContext& ctx = M.getContext ();


            			IRBuilder<> builder(I);
                        Constant* str_const = ConstantDataArray::getString(
                                                                M.getContext(),
                                                                File,
                                                                true);

                        GlobalVariable* fileStr = new GlobalVariable(M,
                                                    str_const->getType(),
                                                    true,
                                                    llvm::GlobalValue::InternalLinkage , 
                                                    str_const
                                                    );
                        AllocaInst *str_alloc = builder.CreateAlloca(PointerType::get(Type::getInt8Ty(M.getContext()), 0));
                        // Value *i32zero = ConstantInt::get(Type::getInt64Ty(M.getContext()), 0);
                        // Value *indices[2] = {i32zero, i32zero};
                        // builder.CreateInBoundsGEP(str_const, ArrayRef<Value *>(indices, 2));

                        Constant* constZeroFmt  = ConstantInt::get(Type::getInt32Ty(M.getContext()), 0);
                        Constant* constArrayFmt = ConstantExpr::getInBoundsGetElementPtr(str_const->getType(),fileStr, constZeroFmt);
                        Value* fmtPtr = ConstantExpr::getBitCast(constArrayFmt, PointerType::getUnqual(Type::getInt8Ty(M.getContext())));

                        builder.CreateStore(fmtPtr, str_alloc);
                        LoadInst *loadVal = builder.CreateLoad(str_alloc);
                        ConstantInt *con_srcline=ConstantInt::get(Type::getInt32Ty(M.getContext()),Line,false);

                        //four parementers
                        Value *intFormat = builder.CreateGlobalStringPtr("filename=%s:srcline=%d,srclen=%d,length=%d\n");
                        vector<Value*> args;
                        Value* next = builder.CreateLoad(pfile);
                        args.push_back(next);
            
                        args.push_back(intFormat);
                        args.push_back(loadVal);
                        args.push_back(con_srcline);
                        args.push_back(arg2_int);
                        args.push_back(val);
                        errs()<<*val<<"\n";

                        
                        Function* funcFprintf ;
                        funcFprintf= M.getFunction("fprintf");
                        if (!funcFprintf)
                        {
                            funcFprintf = getfprint(M, ctx, args);
                        }
                        
                        
                        IRBuilder<> ThenB(I);
                        errs()<<*funcFprintf<<"\n";

                       ThenB.CreateCall(funcFprintf,args);


                        
           
            return true;
        }

        vector<string> split(const string &str, const string &pattern)
        {
            vector<string> res;
            if(str == "")
                return res;
            //在字符串末尾也加入分隔符，方便截取最后一段
            string strs = str + pattern;
            size_t pos = strs.find(pattern);

            while(pos != strs.npos)
            {
                string temp = strs.substr(0, pos);
                res.push_back(temp);
                //去掉已分割的字符串,在剩下的字符串中进行分割
                strs = strs.substr(pos+1, strs.size());
                pos = strs.find(pattern);
            }

            return res;
        }


		bool runOnModule(Module &M) override
		{
             string xmlfilename;
            for(auto &e : getxmlfilename) 
            {
                string s(1,e);
                xmlfilename.append(s);         
            }
            errs()<<M.getName().str()<<"\n";
            LLVMContextImpl* C = M.getContext().pImpl;
            // for (StringMap<StructType *>::iterator i = C->NamedStructTypes.begin(); i != C->NamedStructTypes.end(); ++i)
            //     {
            //         StructType *t = i->getValue();
            //         errs()<<t->getName().str()<<"\n";
            //         // t->dump(); fprintf(stderr, "\n");
            //     }
            if (StructType *filetype= C->NamedStructTypes.lookup("struct._IO_FILE"))

            {
                IO_FILE_ty=filetype;
            }else
            {
                IO_FILE_ty = StructType::create(M.getContext(), "struct._IO_FILE");
            }
			
            IO_FILE_PTR_ty = PointerType::getUnqual(IO_FILE_ty);
            const char* xmlPath=xmlfilename.c_str();
            XMLDocument doc;
            XMLElement * root ;

            ifstream fin(xmlPath);
            if(fin)
            {
                XMLError error = doc.LoadFile(xmlPath);
                if (error != XMLError::XML_SUCCESS)
                    return false;
    
                root = doc.RootElement();
                for (XMLElement* current = root->FirstChildElement(); current != nullptr; current = current->NextSiblingElement())
                {
                    XMLElement* temp = current;
                    string funname=temp->Attribute("funname");
                    string srcline=temp->Attribute("srcline");
                    string Type=temp->Attribute("Type");
                    string bound=temp->Attribute("bound");
                    string mapvalue=srcline+":"+Type+":"+bound;
                     if (functionmap.find(funname) != functionmap.end())
                     {
                        if (std::find(functionmap[funname].begin(), functionmap[funname].end(), mapvalue) != functionmap[funname].end())
                        {
                            continue;
                        }else
                        {
                            functionmap[funname].push_back(mapvalue);
                        }                       
                        
                     }else
                     {
                        std::vector<string> v;
                        v.push_back(mapvalue);
                        functionmap.insert(pair<string, std::vector<string> >(funname,v));
                     }
                    // errs()<<funname<<"\n";
                    // errs()<<mapvalue<<"\n";
                    
                }
    
      
            }
            else
            {
                errs()<<xmlPath<<" is not existens\n";
                return false;
            }


            for(Module::iterator F = M.begin(), E = M.end(); F!= E; ++F) 
            {
                string funname;
                string InLine;
                
                string overtype;
                string sbound;           
               
                string name=F->getName().str();
                funname=name;

                // int num;
                std::vector<string> v;
                if (functionmap.find(name) != functionmap.end())
                {
                    v=functionmap[name];
                    // num=v.size();

                    // for (auto i = v.begin(); i < v.end(); i++)
                    // {
                    //     errs() << *i << " \n";
                    // }
                    // string value=v[1];
                    // errs()<<value<<"\n";
                    // vector<string> res = split(value, ":");
                    // InLine=res[0];
                    // overtype=res[1];
                    // sbound=res[2];
                }else
                {
                    continue;
                }
                // unsigned inLine=stoi(InLine);
                // unsigned bound=stoi(sbound);

                // errs()<<funname<<"\n";
                // errs()<<InLine<<"\n";

                // errs()<<overtype<<"\n";

                // errs()<<sbound<<"\n";

                // if (funname!="CWE126_Buffer_Overread__char_alloca_loop_02_bad")
                // {
                //     return false;
                // }
        for(auto i = v.begin(); i < v.end(); i++)
        {
             string value=*i;
            errs()<<value<<"\n";
            vector<string> res = split(value, ":");
            InLine=res[0];
            overtype=res[1];
            sbound=res[2];
            unsigned inLine=stoi(InLine);
            unsigned bound=stoi(sbound);

          


			for (auto bb_iter=F->begin();bb_iter!=F->end();++bb_iter)
			{
				bool flags=false;
				int counter=0;
				Instruction *firstinst;
				for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
				{
					unsigned Line;
                    string File;

                  	if (DILocation *Loc = ins_iter->getDebugLoc())
								{
																						
									
                  				 	Line = Loc->getLine();
                                 
                                    File = Loc->getFilename().str();
                  					
          						}
          			if (Line==inLine && counter==0)
          			{
          				firstinst=&*ins_iter;
          				counter++;
          			}

          			if (Line==inLine && overtype=="for")
          			{
          				if (StoreInst *storeinst=dyn_cast<StoreInst>(ins_iter))
						{
							//src systax
							Value *storevalue=storeinst->getOperand(0);
							Instruction *loadinst=dyn_cast<Instruction>(storevalue);
							Value *incval;

							Value *loadvalue=loadinst->getOperand(0);
							string strname=loadvalue->getName().str();
							if (strname.substr(0,7)=="arrayid")
							{
								
								Instruction *arrayinst=dyn_cast<Instruction>(loadvalue);
								//int num=arrayinst->getNumOperands();
								//Value *arrayval=arrayinst->getOperand(0);
								incval=arrayinst->getOperand(1);
								errs()<<*incval<<"\n";
								errs()<<*(incval->getType());
								
							}
							IRBuilder<> builder_max(&*ins_iter);
							Value *lencast=builder_max.CreateIntCast(incval,Type::getInt32Ty(F->getContext()),false);

							ConstantInt *con_int=ConstantInt::get(Type::getInt32Ty(F->getContext()),bound,false);
                  			
                  			
                  			Value *cmplt=builder_max.CreateICmpSGT(lencast,con_int);

                        		BranchInst *BI = cast<BranchInst>(
                       	 			SplitBlockAndInsertIfThen(cmplt, &*ins_iter, false));
                        		BasicBlock *thenbb=BI->getParent ();
                        		Instruction *pfilealloca= insertOnMainEntryBlock(*thenbb, M,BI);
                        		insertprintf(BI,*(BI->getModule ()),incval,pfilealloca,File,Line,con_int);
                        		insertOnMainEndBlock(*thenbb,BI,*(BI->getModule ()),pfilealloca);

          						flags=true;
          						break;

							
						}


          			}

          			if (Line==inLine && overtype=="mem")
          			{
          				
                        // Value *cmp_value = builder_max.CreateICmpSGT(llvm_alloca_inst, llvm_alloca_inst_b);
          				//bb_iter->splitBasicBlock(&*ins_iter,"BBB");
          				if (CallInst *call= dyn_cast<CallInst>(ins_iter))
          				{
                            string name;
          					if (Function *fun=call->getCalledFunction())
                            {
                                name=fun->getName().str();
                            }
                            else
                            {
                                continue;
                            }
          					if (name=="llvm.memmove.p0i8.p0i8.i64" || name=="llvm.memcpy.p0i8.p0i8.i64" || name=="__asan_memcpy" ||name=="__asan_memmove")
          					{

                                errs()<<"instrment_start\n";
          						
                        		IRBuilder<> builder_max(&*ins_iter);
          					
                  				Value *lenvalue=ins_iter->getOperand(2);
                                Value *arg2_int;

                                if (bound==0 || bound==-1)
                                {
                                    Value *arg2= ins_iter->getOperand(1);
                                    Type *arg2type=arg2->getType();
                                    if (PointerType *poiterarg2 = dyn_cast<PointerType>(arg2type))
                                    {
                                        if (IntegerType * intarg=dyn_cast<IntegerType>(poiterarg2->getElementType ()))
                                        {
                                            int lenbit= intarg->getBitWidth ();
                                            if(lenbit==8)
                                            {
                                                
                                                arg2_int=getstrlen(*bb_iter,*(ins_iter->getModule()),&*ins_iter,arg2);
                                            }
                                        }
                                        errs()<<*poiterarg2->getElementType ()<<"\n";
                                    }else
                                    {
                                        errs()<<"need modification!\n";
                                    }
                                    errs()<<*arg2type<<"\n";
                                    errs()<<arg2type->getTypeID()<<"\n";
                                }else
                                {
                                    ConstantInt *con_int=ConstantInt::get(Type::getInt64Ty(F->getContext()),bound,false);
                                    arg2_int=dyn_cast<Value>(con_int);

                                }
                                errs()<<*arg2_int->getType()<<*arg2_int<<"\n";
                                errs()<<*lenvalue->getType()<<"\n";


                  			
                  			//Value *lencast=builder_max.CreateIntCast(lenvalue,Type::getInt32Ty(F->getContext()),false);
                                errs()<<*lenvalue->getType()<<"\n";
                                errs()<<*arg2_int->getType()<<"\n";
                  			Value *cmplt=builder_max.CreateICmpSGT(lenvalue,arg2_int);

                        		BranchInst *BI = cast<BranchInst>(
                       	 			SplitBlockAndInsertIfThen(cmplt, &*ins_iter, false));
                        		BasicBlock *thenbb=BI->getParent ();
                        		Instruction* pfliealloca= insertOnMainEntryBlock(*thenbb, *(BI->getModule ()),BI);
                        		insertprintf(BI,*(BI->getModule ()),lenvalue,pfliealloca,File,Line,arg2_int);
                        		insertOnMainEndBlock(*thenbb,BI,*(BI->getModule ()),pfliealloca);

          						flags=true;
          						break;
          					}
          					
          				}

          			}
          		}
          		if(flags)
          		{
          			break;
          		}
          	}
        }
        }

			
			return false;
		}
			
	};
}

char PProcessPass::ID = 0;
static RegisterPass<PProcessPass> X("process", "proprecess Analyse",
	false, false);
