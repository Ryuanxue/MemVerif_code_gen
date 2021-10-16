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
#include <llvm/IR/Type.h>
#include <fstream>
#include <string>
#include "llvm/IR/DebugInfoMetadata.h"
#include <llvm/Analysis/CFG.h>
#include <stdio.h>
#include <assert.h>

#include <iostream>

#include "llvm/Support/Casting.h"

using namespace llvm;
using namespace std;

namespace 
{
	struct Dw_fun_pt_Pass : public ModulePass 
	{
		static char ID;
		std::string str;
	
		Dw_fun_pt_Pass() : ModulePass(ID)
		{
		}

		// string getFieldName(MDNode* meta,int offset)
		string getFieldName(MDNode* meta)
		{
		    if(!meta)
		    {
		        errs()<<"The meta is NULL\n";
		        return ""; 
		    }   
		    string ss="";
		    //getContext()
		    //getMetadataID
		  //   DINode(LLVMContext &C, unsigned ID, StorageType Storage, unsigned Tag,
		  //        ArrayRef<Metadata *> Ops1, ArrayRef<Metadata *> Ops2 = None)
		  //     : MDNode(C, ID, Storage, Ops1, Ops2) {
		  //   assert(Tag < 1u << 16);
		  //   SubclassData16 = Tag;
		  // }

		    // DINode div(meta->getContext(),meta->getMetadataID());
		    auto *div = dyn_cast<DIVariable>(meta);
		    errs()<<"string1"<<"\n";
			errs()<<*div<<"\n";
		    DIType *dit=div->getType(); 
		    auto dict=dyn_cast<DICompositeType>(dit);
		    // DICompositeType dict=static_cast<DICompositeType>(didt.getTypeDerivedFrom());
		    // DIArray dia=dict.getTypeArray(); 
		    // assert(offset<(int)(dict->getElements());
		    // DIType field=static_cast<DIType>(dict->getElement(offset));
		    // //errs()<<"Field'name is "<<field.getName()<<"\n";
		    // return field.getName();
		    return ss;
		}

		bool runOnModule(Module &M)override
	    {
	    	// for(auto it=M.named_metadata_begin ();it!=M.named_metadata_end();it++)
	    	// {
	    	// 	if (DICompositeType *dict=dyn_cast<DICompositeType>(**it))
	    	// 	{
	    	// 		errs()<<"fffff\n";
	    	// 	}
	    	// 	errs()<<(&it)<<"\n";
	    	// }


			for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
			{
				for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
				{
					int valueid=ins_iter->getValueID ();

					if(GetElementPtrInst *gep=dyn_cast<GetElementPtrInst>(ins_iter))
					{
						int num=gep->getNumOperands();
						if (num>3)
						{
							errs()<<"########################################"<<"\n";
						}
						// errs()<<*gep<<"\n";
					}

					if (const DbgDeclareInst* DbgDeclare = dyn_cast<DbgDeclareInst>(ins_iter))
					{
				      // if (DbgDeclare->getAddress() == V) return DbgDeclare->getVariable();
						Value *val=DbgDeclare->getAddress();
						Type *valtype=val->getType();
						if (PointerType *pt=dyn_cast<PointerType>(valtype))
						{
							Type *eletype=pt->getElementType () ;
							if (PointerType *ptt=dyn_cast<PointerType>(eletype))
							{
								Type *peletype=ptt->getElementType();
								if (StructType *st=dyn_cast<StructType>(peletype))

								{

									DILocalVariable *dlraw=DbgDeclare->getVariable () ; //er 37
 
									// Metadata * mtrawvar=DbgDeclare->getRawVariable () ; 
									DIType *dit=dlraw->getType(); //类型38
									DIDerivedType *didt=dyn_cast<DIDerivedType>(dit);//类型38

									// DIType * mtrawvar=dit->getType() ;
									// DICompositeType *dict=dyn_cast<DICompositeType>(dit->getTypeDerivedFrom());
									int num=didt->getNumOperands () ;
									for (int i=0;i<num;i++)
									{
										const MDOperand &op= didt->getOperand(i);
										if (op)
										{
											errs()<<*op<<"\n";
											DIDerivedType *opddit=dyn_cast<DIDerivedType>(op);//类型39 SSL3_RECORD
											int dnum=opddit->getNumOperands();
											for(int j=0;j<dnum;j++)
											{
												const MDOperand &opp= opddit->getOperand(j);
												if(j==3)
												{
													DICompositeType *dict=dyn_cast<DICompositeType>(opp); //结构体名字40 ssl3_record_st 里面包含成员elements
													DINodeArray narr=dict->	getElements (); //获得成员变量
													int elesize=narr.size();
													for (int m=0;m<elesize;m++)
													{
														DIDerivedType *temp=dyn_cast<DIDerivedType>(narr[m]);


														errs()<<temp->getName()<<"\n";
													}
													errs()<<*opp<<"\n";
												}
												errs()<<opp<<"\n";
											}

										}
										
									}

									 

									errs()<<"ptt"<<"\n";
									errs()<<"declare\n";
									errs()<<*DbgDeclare<<"\n";
									errs()<<*val<<"\n";
									errs()<<*valtype<<"\n";


									errs()<<*dlraw<<"\n";
									errs()<<*dit<<"\n";
									// errs()<<*mtrawvar<<"\n";
									errs()<<num<<"\n";


								}
								
							}
							
						}
						
						
					

				    } else if (const DbgValueInst* DbgValue = dyn_cast<DbgValueInst>(ins_iter)) 
				    {
				      // if (DbgValue->getValue() == V) return DbgValue->getVariable();
				    	errs()<<"dbgvalue\n"; 
						errs()<<*DbgValue<<"\n";
				    }

					 // if (GetElementPtrInst *getinst=dyn_cast<GetElementPtrInst>(ins_iter))
					 // {
					 // // 	int offset=0;
						// // ConstantInt* CI=dyn_cast<ConstantInt>(getinst->getOperand(2));
						// // offset=CI->getSExtValue();
					 // 	MDNode * mds= getinst->getMetadata("dbg");
					 // 	string filename=getFieldName(mds);
					 // 	errs()<<"string"<<"\n";
					 // 	errs()<<*mds<<"\n";

					 // }


			// }
				
	     	
		 // }

	    return false;
	    }


	};
}

char Dw_fun_pt_Pass::ID = 0;
static RegisterPass<Dw_fun_pt_Pass> X("test", "proprecess Analyse",
	false, false);


