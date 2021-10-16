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

#include <iostream>

#include "llvm/Support/Casting.h"

using namespace llvm;
using namespace std;

namespace 
{
	struct Dw_fun_pt_Pass : public FunctionPass 
	{
		static char ID;
		std::string str;
	
		Dw_fun_pt_Pass() : FunctionPass(ID)
		{
		}

		bool runOnFunction(Function &F) override
    {

    	for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
		{
			for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
			{
				int valueid=ins_iter->getValueID ();

				 if (valueid==57)
						{
							StoreInst *storeinst=dyn_cast<StoreInst>(ins_iter);
							

							Value *value1=storeinst->getOperand(0);

							Type *type1=value1->getType();

							if (PointerType *pin=dyn_cast<PointerType>(type1))
							{
								Type *pin_to=pin->getElementType ();
								if (FunctionType *funtype=dyn_cast<FunctionType>(pin_to))
								{

									Value *value2 =storeinst->getOperand(1);

									errs()<<valueid<<"\n";
									errs()<<*storeinst<<"\n";
									// errs()<<*value1<<"\n";
									// errs()<<*value2<<"\n";
									errs()<<*type1<<"\n";

								}
								
							}
							

						}



			
     	}
     }

    return false;
    }


	};
}

char Dw_fun_pt_Pass::ID = 0;
static RegisterPass<Dw_fun_pt_Pass> X("de-fun-pt", "proprecess Analyse",
	false, false);

