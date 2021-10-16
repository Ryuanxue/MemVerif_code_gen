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
#include <iostream>
#include <string>
#include "llvm/IR/DebugInfoMetadata.h"
#include <llvm/Analysis/CFG.h>
#include <stdio.h>
#include <map>
#include "llvm/Support/Casting.h"
using namespace llvm;
#include "llvm/Support/CommandLine.h"
#include <string>
#include <fstream>
#include <codecvt>
#include <cstdio>

static cl::opt<std::string> getfunname("fun-name", cl::desc("Specify function name for mypass"), cl::value_desc("function"));
static cl::opt<std::string> getvarname("var-name", cl::desc("Specify varible name for mypass"), cl::value_desc("varible"));

using namespace std;

namespace {
    struct GetBoundPass : public FunctionPass {
        
        static char ID;
        GetBoundPass():FunctionPass(ID) {}

        bool runOnFunction(Function &M) override{
          string funname;
          for(auto &e : getfunname) {
            string s(1,e);
            funname.append(s);
            //errs() << e << "\n";

          }
          errs()<<funname<<"\n";
          string varname;
          for(auto &var:getvarname){
            string v(1,var);
            varname.append(v);
          }
          errs()<<varname<<"\n";

          string fname=M.getName().str();
          if (fname!=funname){
            return false;

          }
          for (Function::iterator iter = M.begin(); iter != M.end(); ++iter)

          {

            for (BasicBlock::iterator Biter = iter->begin(); Biter != iter->end(); ++Biter)

              {

                Instruction *I = &*Biter;

                
                
                if (AllocaInst *alloca_inst =dyn_cast<AllocaInst>(I)){
                  string variblename=alloca_inst->getName().str();
                  Type *type=alloca_inst->getAllocatedType();
                  if (variblename==varname){
                    if (ArrayType *arrayType=dyn_cast<ArrayType>(type)){
                    errs()<<"True\n";
                    errs()<<arrayType->getNumElements ( )<<"\n";
                    // ofstream oFile;
                    // oFile.open("bound.txt", ios::out);
                    // // oFile<<arrayType->getNumElements ( );
                    // //oFile.write((char*)arrayType->getNumElements ( ),sizeof(arrayType->getNumElements ( )));
                    // oFile.close();
                    
                    ofstream oFile;
                      oFile.open("bound.txt", ios::out);
                      oFile<<arrayType->getNumElements ( );
                      oFile.close();
                    break;
                  }
                  else
                    continue;
                  }else
                  continue;
                }

                // if (CallInst *call = dyn_cast<CallInst>(I)) {
                //   Function *calledFunction = call->getCalledFunction();
                //   std::string name=calledFunction->getName().str();

                //   if (name=="malloc"){
                //      errs()<<*I<<"\n";
                //     errs()<<name<<"\n";
                //     for (auto arg = call->arg_begin(); arg != call->arg_end(); ++ arg) {
                //       if (auto val = dyn_cast<ConstantInt>(arg)) {
                //         errs() << val->getZExtValue() << "\n";
                //   }
                // errs()<<*(call->getFunctionType()->getReturnType())<<"\n";
                //   }

                //   }
                // }
                // 

                if(StoreInst *store =dyn_cast<StoreInst>(I)){
                  
                  std::string storename=I->getOperand(1)->getName();
                  errs()<<storename<<"\n";
                  if (storename==varname){
                     errs()<<*I<<"\n";
                    if(AllocaInst *alloca = dyn_cast<AllocaInst>(I->getOperand(0))){
                      Value *valull=alloca->getOperand(0);
                      Type *valtype=valull->getType();
                      errs()<<*valull<<"\n";
                      
                      if (auto *constint=dyn_cast<ConstantInt>(valull)){
                        errs()<<*alloca<<"\n";
                        errs()<<constint->getZExtValue()<<"\n";
                        unsigned intvalue=constint->getZExtValue();

                       
                    ofstream oFile;
                      oFile.open("bound.txt", ios::out);
                      oFile<<constint->getZExtValue();
                      oFile.close();
                      //   string_convert<codecvt_utf8<wchar_t>> conv;
 
                      //   string narrowStr = conv.to_bytes(intvalue);

                      //   ofstream oFile;
                      // oFile.open("bound.txt", ios::out);
                      // oFile<<narrowStr;
                      // // oFile.write((char*)&intvalue,sizeof(intvalue));
                      // oFile.close();
                        break;
                      }

                    }
                    if (BitCastInst *bitcast=dyn_cast<BitCastInst>(I->getOperand(0))){
                      errs()<<bitcast->getNumOperands()<<"\n";
                      Value *bitvalue = bitcast->getOperand(0);
                      errs()<<*bitvalue;

                       if (CallInst *call = dyn_cast<CallInst>(bitvalue)) {
                  Function *calledFunction = call->getCalledFunction();
                  string name=calledFunction->getName().str();

                  if (name=="malloc"){
                    errs()<<name<<"\n";
                    Value *arg=call->getArgOperand (0);
                    Type *rettype= call->getFunctionType()->getReturnType();
                    
                    PointerType *ptype=dyn_cast<PointerType>(rettype);
                    unsigned size=ptype->getContainedType(0)->getIntegerBitWidth ();

                    ConstantInt *val = dyn_cast<ConstantInt>(arg);
                    errs() << size << "\n";
                    unsigned byte=val->getZExtValue() ;

                    errs()<<byte <<"\n";

                    unsigned bound=byte/size;
                    
                    // errs()<<bound;
                     ofstream oFile;
                      oFile.open("bound.txt", ios::out);
                      oFile<<bound;
                      oFile.close();
                

                  }
                }
                    }
                    
                  }
                }
                
              } 
          }
          return false;

        }
    };
}


// Register the pass with llvm, so that we can call it with dummypass
char GetBoundPass::ID = 0;
static RegisterPass<GetBoundPass> X("getboundpass", "Example LLVM pass printing each function it visits");
