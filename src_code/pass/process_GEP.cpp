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
	struct Process_GEP_Pass : public FunctionPass 
	{
		static char ID;
		std::string str;
	
		Process_GEP_Pass() : FunctionPass(ID)
		{
		}

		int get_struct_array_bound(Type* val_ty,int index)
	    {
	      int arraybound=0;
	       // val_ty是struct type
	      Type *membertype=val_ty->getStructElementType(index);
	      errs()<<*membertype<<"\n";

	      if (ArrayType *srcarraytype=dyn_cast<ArrayType>(membertype))
                        {
                          arraybound=srcarraytype->getNumElements () ;

                        }else 
                        {
                        	errs()<<"bound_continue\n";
                        }

	      return arraybound;
	    }

       int deal_with_gep(int num,Instruction *ins_iter,char *srcname,Function &F)
       {
                     
                     errs()<<"deal_with_gep_start\n";
                     int bound=0;
                     memcpy(srcname,"non__struct__",14);

                     Type *geptype=ins_iter->getType();   
                        if(num==2)
                        { //
                          Value *firstop=ins_iter->getOperand(0);
                          errs()<<num<<"_111\n";
                          if (firstop->getValueID()==56)
                          {
                            errs()<<*firstop->getType()<<"\n";
                            if (firstop->getType()==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                            {
                              memcpy(srcname,"struct",7);
                              bound=0;
                              errs()<<srcname<<"\n";
                              
                            }else
                            {
                              //phi instruction
                              //GEP instruction
                              //select instruction t1_enc.c
                            	bound=0;
                              errs()<<"num2_continue1"<<"\n";
                            }

                          
                          }else if(firstop->getValueID()==17)
                          {
                            memcpy(srcname,"struct",7);
                            bound=0;
                              errs()<<srcname<<"\n";
                              
                          }

                          else
                          {
                          	//phi
                          	//gep
                            errs()<<*firstop<<"\n";
                            errs()<<"num2_continue2"<<"\n";
                          }
                          
                        }

                        if (num==3)
                        {
                         errs()<<"33333\n";
                          errs()<<*ins_iter->getType()<<"\n";
                          PointerType *pin=dyn_cast<PointerType>(ins_iter->getType());
                      
                          Type *pinele=pin->getElementType ();
                          errs()<<*pinele<<"\n";               

                          if (ConstantInt *cons=dyn_cast<ConstantInt>(ins_iter->getOperand(num-1)))
                          {
                            uint64_t consvalue=cons->getZExtValue ();

                          Type* srctype= dyn_cast<GetElementPtrInst >(ins_iter)->getSourceElementType ();
                            errs()<<*srctype<<"\n";
                            if (ArrayType *srcarraytype=dyn_cast<ArrayType>(srctype))
                            {
                              bound=srcarraytype->getNumElements () ;
                              
                              
                              errs()<<bound<<"\n";

                            }


                              else if (consvalue==0)
                              {
                                errs()<<num<<"\n";
                              
                          
                                
                                errs()<<*srctype<<"\n";
                                llvm::DataLayout* dl = new llvm::DataLayout(ins_iter->getModule ());
                                uint64_t myStructSuze = dl->getTypeStoreSize(srctype);
                                errs()<<myStructSuze<<"\n";
                                bound=myStructSuze;

                              

                              }else
                              {

                                errs()<<"num3_continue"<<"\n";
                              }
                            }  
                        }



                        if (num==4)
                        {
                          Type* srctype= dyn_cast<GetElementPtrInst >(ins_iter)->getSourceElementType ();
                          errs()<<*ins_iter->getType()<<"\n";
                          PointerType *pin=dyn_cast<PointerType>(ins_iter->getType());
                          
                          Type *pinele=pin->getElementType ();
                          errs()<<*pinele<<"\n";
                          if (pinele==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                          {
                          	bound=0;
                          	memcpy(srcname,"struct",30);
                          }
                          
                          else if (ConstantInt *cons=dyn_cast<ConstantInt>(ins_iter->getOperand(num-1)))
                          {
                            uint64_t consvalue=cons->getZExtValue ();
                            
                              if (consvalue==0)
                              {
                                errs()<<num<<"\n";
                                uint64_t index=dyn_cast<ConstantInt>(ins_iter->getOperand(2))->getZExtValue ();
                                errs()<<*srctype<<"\n";
                                bound=get_struct_array_bound(srctype,index);
                                
                                errs()<<bound<<"\n";

                              }else if(geptype==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                              { 
                              uint64_t index=dyn_cast<ConstantInt>(ins_iter->getOperand(2))->getZExtValue ();
                                int abound=get_struct_array_bound(srctype,index);
                                bound=abound- consvalue;
                                
                                errs()<<abound- consvalue <<"\n";
                            } else
                            {
                              
                              errs()<<"num4_continue1"<<"\n";
                            }
                          }else if (geptype==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                          {
                            // bound is a varible
                            uint64_t index=dyn_cast<ConstantInt>(ins_iter->getOperand(2))->getZExtValue ();

                            int abound=get_struct_array_bound(srctype,index);
                            bound=-10;
                            
                                errs()<<bound<<"\n";
                            errs()<< *srctype->getStructElementType(index) <<"\n";
                            errs()<<"bound is a varible"<<"\n";
                          }else
                          {
                            errs()<<"num4_continue2"<<"\n";
                          }
                            
                        }


                        if(num>4)
                        {

                          if (ConstantInt *cons=dyn_cast<ConstantInt>(ins_iter->getOperand(num-1)))
                          {
                            uint64_t consvalue=cons->getZExtValue ();
                            if (consvalue==0)
                            {
                             

                              errs()<<num<<"\n";
                  
                              Type* srctype= dyn_cast<GetElementPtrInst >(ins_iter)->getSourceElementType ();

                              Type *temptype=srctype;
                              for (int i=2;i<num-1;i++)
                              {
                                errs()<<*temptype<<"\n";

                                int index=dyn_cast<ConstantInt>(ins_iter->getOperand(i))->getZExtValue ();
                                if (i!=num-2)
                                {
                                temptype=temptype-> getStructElementType(index);
                                 if (ArrayType *srcarraytype=dyn_cast<ArrayType>(temptype))
                                 {
                                  break;
                                 }
                                
                                }else
                                {
                                  bound =get_struct_array_bound (temptype,index);
                                  
                                  errs()<<bound<<"\n";
                                }

                              }
       
                            }
                          }else{
                            errs()<<"num5_continue"<<"\n";
                          } 

                        }
                        return bound;
       }


	    Type *get_struct_type(Type* val_ty,int index)
	    {
	    	Type *membertype=val_ty->getStructElementType(index);
	    	return membertype;

	    }


  int deal_with_load(LoadInst *srcload,Value *val,char *parm_srcname,Function &F)
                          {
                            int bound=0;
                            memcpy(parm_srcname,"non__struct__",14);
                            if (val->getValueID()==55)
                            {
                              //src name
                              string srcname=srcload->getOperand(0)->getName().str();
                              errs()<<srcname.c_str()<<"444\n";
                              memcpy(parm_srcname,srcname.c_str(),strlen(srcname.c_str()));
                              bound=0;
                            }
                            else if (val->getValueID()==58)
                            {
                              int num=dyn_cast<Instruction>(val)->getNumOperands();
                                                   
                                
                                bound=deal_with_gep(num,dyn_cast<Instruction>(val),parm_srcname,F);
                                
                            }else
                            {
                            	bound=0;
                            	
                              errs()<<val->getValueID()<<"loadsrcid_continue\n";
                               errs()<<*val<<"\n";
                            }
                            return bound;


                          }

 void deal_with_phi(int num,Instruction *ins_iter,std::vector<char *> &name_ret,std::vector<int> &size_ret,Function &F)
  {
  	for (int i=0;i<num;i++)
						{

							Value *srcvalue=ins_iter->getOperand(i);
							int valid=srcvalue->getValueID();
							errs()<<*ins_iter->getOperand(i)<<"\n";
							char *parm_srcname=NULL;
	                            parm_srcname=(char*)malloc(30*sizeof(char));  
	                            memset(parm_srcname,30,'\0');
	                            memcpy(parm_srcname,"non__struct__",14);
	                            int bound=0;
                            
							
							if(valid==56)
							{
								 LoadInst *srcload=dyn_cast<LoadInst>(srcvalue);
                  				Value *val=srcload->getOperand(0);
	                          	
                            

	                            bound=deal_with_load(srcload,val,parm_srcname,F);
	                            name_ret.push_back(parm_srcname);
	                            size_ret.push_back(bound);

	            
                                errs()<<bound<<"\n";
                                errs()<<parm_srcname<<"\n";
                               

							}

							else if(valid==58)
							{
								
		                      	Type *geptype=dyn_cast<Instruction>(srcvalue)->getType();
		                      	int num=dyn_cast<Instruction>(srcvalue)->getNumOperands();
	                      	
		                      	errs()<<*srcvalue<<"\n";
		                      	bound=deal_with_gep(num,dyn_cast<Instruction>(srcvalue),parm_srcname,F);
		                      	name_ret.push_back(parm_srcname);
	                            size_ret.push_back(bound);
		                      	errs()<<bound<<"\n";
		                      	
							}

							else if(valid==79)
							{
								errs()<<*srcvalue<<"\n";
								int num1=dyn_cast<Instruction>(srcvalue)->getNumOperands();
								deal_with_phi(num1,dyn_cast<Instruction>(srcvalue),name_ret,size_ret,F);

							}else
							{
								errs()<<srcvalue<<"\n";
								errs()<<"79_continue"<<"\n";
								
							}
						}
  }

    bool runOnFunction(Function &F) override
    {

    	for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
		{
			for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
			{
				int valueid=ins_iter->getValueID ();


					// if ( valueid==58)//getElementPtr
     //                  {
     //                  	errs()<<*ins_iter<<"\n";
     //                  	errs()<<*ins_iter->getType()<<"\n";
     //                  	Type *geptype=ins_iter->getType();
     //                  	int num=ins_iter->getNumOperands();

     //                  	char *srcname=NULL;
     //                  	srcname=(char*)malloc(20*sizeof(char));

     //                  	int bound;
                      	
     //                  	bound=deal_with_gep(num,&*ins_iter,srcname,F);
     //                  	errs()<<srcname<<"\n";
     //                  	errs()<<bound<<"\n";
     //                  	free(srcname);                            
                        
     //                  }
				int length=-2;
				string srcname="";
				errs()<<srcname<<" 111\n";
				int bound;

					if (valueid==79)
					{
						int num=ins_iter->getNumOperands();
						std::vector<int> size_ret;
						std::vector<char *> name_ret;
						

						deal_with_phi(num,&*ins_iter,name_ret,size_ret,F);
						errs()<<"length"<<"\n";
						for (auto inter=size_ret.begin();inter!=size_ret.end();inter++)
						{
							errs()<<*inter<<"\n";
						}
						errs()<<"output_string"<<"\n";
						for (auto inter=name_ret.begin();inter!=name_ret.end();inter++)
						{
							errs()<<*inter<<"\n";
						}



						// for (int i=0;i<num;i++)
						// {

						// 	Value *srcvalue=ins_iter->getOperand(i);
						// 	int valid=srcvalue->getValueID();
						// 	errs()<<*ins_iter->getOperand(i)<<"\n";
							
						// 	if(valid==56)
						// 	{
						// 		 LoadInst *srcload=dyn_cast<LoadInst>(srcvalue);
      //             				Value *val=srcload->getOperand(0);
	     //                      char *parm_srcname=NULL;
	     //                        parm_srcname=(char*)malloc(30*sizeof(char));  
	     //                        memset(parm_srcname,30,'\0');
                            

	     //                        bound=deal_with_load(srcload,val,parm_srcname,F);

	     //                        if (parm_srcname[0]!='\0')
      //                           {
      //                           	errs()<<parm_srcname<<" 222\n";
      //                             srcname=parm_srcname;
      //                           }
      //                           if (length==bound)
      //                           {
      //                             length=-2;
      //                             continue;
      //                           }
      //                           errs()<<srcname<<"\n";
      //                           errs()<<srcname<<" 333\n";
      //                           errs()<<bound<<"\n";
      //                           free(parm_srcname);

						// 	}

						// 	else if(valid==58)
						// 	{
								
		    //                   	Type *geptype=dyn_cast<Instruction>(srcvalue)->getType();
		    //                   	int num=dyn_cast<Instruction>(srcvalue)->getNumOperands();

		    //                   	char *parm_srcname=NULL;
		    //                   	parm_srcname=(char*)malloc(30*sizeof(char));

		    //                   	int bound;
		    //                   	errs()<<*srcvalue<<"\n";
		    //                   	bound=deal_with_gep(num,dyn_cast<Instruction>(srcvalue),parm_srcname,F);
		    //                   	errs()<<srcname<<"\n";
		    //                   	errs()<<bound<<"\n";
		    //                   	free(parm_srcname); 
						// 	}

						// 	else if(valid==79)
						// 	{
						// 		errs()<<srcvalue<<"\n";
						// 		errs()<<"79_continue"<<"\n";

						// 	}

							

						// }
						errs()<<*ins_iter<<"\n";
						errs()<<"\n";

						
	        		}
				}

     	}

    return false;
    }


	};
}

char Process_GEP_Pass::ID = 0;
static RegisterPass<Process_GEP_Pass> X("GEP", "proprecess Analyse",
	false, false);


