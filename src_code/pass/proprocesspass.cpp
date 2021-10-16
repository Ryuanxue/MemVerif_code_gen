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
 #include<set>
#include <map>
#include <iostream>
#include <algorithm>
#include "tinyxml2.h"
#include "llvm/Support/CommandLine.h"
 
using namespace tinyxml2;
#include "llvm/Support/Casting.h"

using namespace llvm;
using namespace std;

static cl::opt<std::string> getxmlfilename("xmlfile", cl::desc("Specify function name for mypass"), cl::value_desc("xmlfilename"));



namespace 
{
	struct PProcessPass : public FunctionPass 
	{
		static char ID;
		std::string str;
	
		PProcessPass() : FunctionPass(ID)
		{
		}


		void create_xml(const char* xmlPath,const char* type,
          			const char* c_filename,
          			int startline,
          			int endline,
          			const char* funname,
          			const char* srcname,
          			int srcline,
          			const char* incname,
          			const char* len_three,
                int bound)
		{
			std::cout << "\ncreate_xml2:" << xmlPath << std::endl;
			//【】构造一个xml文档类
			XMLDocument doc;
			XMLElement * root ;

			ifstream fin(xmlPath);
  			if(!fin)
  			{
  			XMLDeclaration * declaration = doc.NewDeclaration();
			doc.InsertFirstChild(declaration);
			root= doc.NewElement("Root");
			doc.InsertEndChild(root);
      
 			}
 			else
 			{
 			XMLError error = doc.LoadFile(xmlPath);
			if (error != XMLError::XML_SUCCESS)
				return;
	
			root = doc.RootElement();


 			}
	
			XMLElement * element = root->InsertNewChildElement("ovreadsrc");
			element->SetAttribute("Type", type);
			element->SetAttribute("c_filename",c_filename);
			element->SetAttribute("startline",startline);
			element->SetAttribute("endline",endline);
			element->SetAttribute("funname",funname);
			element->SetAttribute("srcname",srcname);
			element->SetAttribute("incname",incname);
			element->SetAttribute("srcline",srcline);
			element->SetAttribute("len_three",len_three);
      element->SetAttribute("bound",bound);
			
 
	
			doc.SaveFile(xmlPath);
		}


    int get_struct_array_bound(Type* val_ty,int index,Instruction *ins_iter)
      {
        int arraybound=0;
         // val_ty是struct type
        Type *membertype=val_ty->getStructElementType(index);
        errs()<<*membertype<<"\n";

        if (ArrayType *srcarraytype=dyn_cast<ArrayType>(membertype))
                        {
                          arraybound=srcarraytype->getNumElements () ;
                           

                          // cout<<bound;
                        }else if( StructType* strcttype=dyn_cast<StructType>(membertype))
                        {
                          llvm::DataLayout* dl = new llvm::DataLayout(ins_iter->getModule ());
                                arraybound = dl->getTypeStoreSize(membertype);
                          
                        }else
                        {
                          errs()<<*membertype<<"bound_continue\n";
                          errs()<<"bound_continue\n";
                        }

        return arraybound;
      }



    int deal_with_gep(int num,Instruction *ins_iter,char *srcname,Function &F,std::vector<string> &inst_name)
       {

                     
                     errs()<<"deal_with_gep_start\n";
                     errs()<<ins_iter->getName().str()<<"\n";
                     int bound=0;
                     
                     
                    if (std::find(inst_name.begin(), inst_name.end(), ins_iter->getName().str()) != inst_name.end())
                              {
                                return bound;
                              }
                              inst_name.push_back(ins_iter->getName().str());

                     Type *geptype=ins_iter->getType();   
                        if(num==2)
                        { //
                          Value *firstop=ins_iter->getOperand(0);
                          errs()<<num<<"_111\n";
                           errs()<<*firstop<<"_111\n";

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

                          else if(firstop->getValueID()==79)
                          {
                            errs()<<"deal_with_phi"<<"\n";
                            std::vector<char *> name_ret;
                            std::vector<int> size_ret;
                            int num1=dyn_cast<Instruction>(firstop)->getNumOperands();
                             errs()<<*firstop<<"_111\n";
                             Instruction *tempins=dyn_cast<Instruction>(firstop);
                             errs()<<*tempins<<"\n";
                            deal_with_phi(num1,tempins,name_ret,size_ret,F,inst_name);

                            for (auto inter=size_ret.begin();inter!=size_ret.end();inter++)
                            {
                              if (*inter>0)
                              {
                                bound=*inter;
                                break;
                              }
                              errs()<<*inter<<"\n";
                            }
                            
                            for (auto inter=name_ret.begin();inter!=name_ret.end();inter++)
                            {
                              if (!strcmp(*inter,"struct"))
                              {
                                memcpy(srcname,*inter,7);
                                break;
                              }
                              errs()<<*inter<<"\n";
                            }

                          }else if(firstop->getValueID()==58)
                          {
                            int num1=dyn_cast<Instruction>(firstop)->getNumOperands();
            
                                bound=deal_with_gep(num1,dyn_cast<Instruction>(firstop),srcname,F,inst_name);

                          }
                          else if(firstop->getValueID()==81)
                          {

                            Value *opvalue1=dyn_cast<Instruction>(firstop)->getOperand(1);
                            Value *opvalue2=dyn_cast<Instruction>(firstop)->getOperand(2);
                            if ((opvalue1->getValueID()==58)&&(opvalue2->getValueID()==58))
                            {
                              int num1=dyn_cast<Instruction>(opvalue1)->getNumOperands();
            
                                int bound1=deal_with_gep(num1,dyn_cast<Instruction>(opvalue1),srcname,F,inst_name);
                            
                              int num2=dyn_cast<Instruction>(opvalue2)->getNumOperands();
            
                                int bound2=deal_with_gep(num1,dyn_cast<Instruction>(opvalue2),srcname,F,inst_name);

                                if (bound1==bound2)
                                {
                                  bound=bound1;
                                }
                            }else
                            {
                              errs()<<*opvalue1<<"\n";
                             errs()<<opvalue1->getValueID()<<"\n";
                             errs()<<*opvalue2<<"\n";
                             errs()<<opvalue2->getValueID()<<"\n";
                             errs()<<"num2_continue2"<<"\n";

                            }


                          }else
                          {
                            //phi
                            //gep
                            
                            errs()<<*firstop<<"\n";
                             errs()<<firstop->getValueID()<<"\n";
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

                          if (pinele==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                          {
                            bound=0;
                            memcpy(srcname,"struct",30);
                          }
                          else if (ConstantInt *cons=dyn_cast<ConstantInt>(ins_iter->getOperand(num-1)))
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

                              

                              }else if(consvalue>0)
                              {
                                bound =get_struct_array_bound(geptype,consvalue,ins_iter);

                               
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
                                bound=get_struct_array_bound(srctype,index,ins_iter);
                                
                                errs()<<bound<<"\n";

                              }else if(geptype==PointerType::get(Type::getInt8Ty(F.getContext()), 0))
                              { 
                              uint64_t index=dyn_cast<ConstantInt>(ins_iter->getOperand(2))->getZExtValue ();
                                int abound=get_struct_array_bound(srctype,index,ins_iter);
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

                            int abound=get_struct_array_bound(srctype,index,ins_iter);
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
                                  bound =get_struct_array_bound (temptype,index,ins_iter);
                                  
                                  errs()<<bound<<"\n";
                                }

                              }
       
                            }
                          }else{
                            errs()<<"num5_continue"<<"\n";
                          } 

                        }
                        errs()<<srcname<<"jjjjjjjjj";
                        return bound;
       }
 

 
  int deal_with_load(LoadInst *srcload,Value *val,char *parm_srcname,Function &F,std::vector<string> &inst_name)
                          {
                            
                            int bound=0;
                      


                              if (std::find(inst_name.begin(), inst_name.end(), srcload->getName().str()) != inst_name.end())
                              {
                                return bound;
                              }
                              inst_name.push_back(srcload->getName().str());

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
                                                   
                                
                                bound=deal_with_gep(num,dyn_cast<Instruction>(val),parm_srcname,F,inst_name);
                                
                            }else
                            {
                              bound=0;
                              
                              errs()<<val->getValueID()<<"loadsrcid_continue\n";
                               errs()<<*val<<"\n";
                            }
                            return bound;


                          }


 void deal_with_phi(int num,Instruction *ins_iter,std::vector<char *> &name_ret,std::vector<int> &size_ret,Function &F,std::vector<string> &inst_name)
  {
    
    if (std::find(inst_name.begin(), inst_name.end(), ins_iter->getName().str()) != inst_name.end())
                              {
                                return;
                              }
                              inst_name.push_back(ins_iter->getName().str());
                              int bound=0;

    for (int i=0;i<num;i++)
            {


              Value *srcvalue=ins_iter->getOperand(i);
              int valid=srcvalue->getValueID();
              errs()<<*ins_iter->getOperand(i)<<"\n";
              errs()<<"start_deal_with_phi"<<"\n";
              errs()<<*ins_iter<<"\n";
              char *parm_srcname=NULL;
                              parm_srcname=(char*)malloc(30*sizeof(char));  
                              memset(parm_srcname,30,'\0');
                              memset(parm_srcname,'\0',30);
                              int bound=0;
                            
              
              if(valid==56)
              {
                 LoadInst *srcload=dyn_cast<LoadInst>(srcvalue);
                          Value *val=srcload->getOperand(0);
                              
                            

                              bound=deal_with_load(srcload,val,parm_srcname,F,inst_name);
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
                            bound=deal_with_gep(num,dyn_cast<Instruction>(srcvalue),parm_srcname,F,inst_name);
                            name_ret.push_back(parm_srcname);
                              size_ret.push_back(bound);
                            errs()<<bound<<"\n";
                            
              }

              else if(valid==79)
              {
                errs()<<*srcvalue<<"\n";
                int num1=dyn_cast<Instruction>(srcvalue)->getNumOperands();
                deal_with_phi(num1,dyn_cast<Instruction>(srcvalue),name_ret,size_ret,F,inst_name);


              }else if(valid==80)
              {
                memcpy(parm_srcname,"struct",7);
                name_ret.push_back(parm_srcname);
                              size_ret.push_back(bound);
                
                
              }else if(valid==15)
              {

              }

              else
              {
                Type *temptype=srcvalue->getType();
                if(temptype==PointerType::get(Type::getInt64Ty(F.getContext()), 0))
                {

                }
                errs()<<valid<<"\n";
                errs()<<"79_continue"<<"\n";
              }
            }
  }

		bool runOnFunction(Function &F) override
		{
      string xmlfilename;
            for(auto &e : getxmlfilename) 
            {
                string s(1,e);
                xmlfilename.append(s);         
            }
			set<int> linenum;
			for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
			{
				for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
				{
					unsigned Line;

                  	if (DILocation *Loc = ins_iter->getDebugLoc())
								{
																						
									
                  Line = Loc->getLine();
                  if (Line==0)
                  {
                    continue;
                  }
                  linenum.insert(Line);
          			}
        }

      }
      

      if(linenum.empty())
      {
        return false;
      }

			for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
			{
				for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
				{
					unsigned Line;

                  	string File;
                  	string Dir;	
                  	if (DILocation *Loc = ins_iter->getDebugLoc())
								{
																						
									
                  Line = Loc->getLine();
                  File = Loc->getFilename().str();
                  Dir = Loc->getDirectory().str();
          			}

          			string type="";
          			string c_filename="";
          			int startline=0;
          			int endline=0;
          			string funname="";
          			string srcname="";
          			int srcline=0;
          			string incname="";
          			string len_three="";
                int bound=0;

          			c_filename=File;
					startline=*(linenum.begin());
					endline=*(linenum.rbegin());
					//cout<<"endline "<<endline<<endl;
					funname=F.getName().str();
					srcline=Line;

          			//errs()<<ins_iter->getOpcodeName () <<"\n";
					if(CallInst *call = dyn_cast<CallInst>(ins_iter))
					{
						Function *calledFunction = call->getCalledFunction  ();
            if (!calledFunction)
            {
              continue;
            }
            
              string name=calledFunction->getName().str();
                 
                      
            if ((name=="llvm.memcpy.p0i8.p0i8.i64" )|| (name=="llvm.memmove.p0i8.p0i8.i64") || name=="__asan_memcpy" ||name=="__asan_memmove")
            {
              //errs()<<name<<"\n";
              type="mem";
              incname="";

              unsigned size;
              errs()<<"mem"<<" "<<File<<" "<<Line<<" "<<*ins_iter<<" \n";

              // get second paremeter of memcpy function
              std::vector<string> inst_name;
              Value *srcvalue=ins_iter->getOperand(1);
              //inst_name.push_back(srcvalue->getName().str());
              Value *three=ins_iter->getOperand(2);
              uint64_t length=-2;

              if(ConstantInt *cons=dyn_cast<ConstantInt>(three))
              {
                 length=cons->getZExtValue ();
                errs()<<length <<"\n";
              }

              const DebugLoc &location = ins_iter->getDebugLoc();
              errs()<<location.getLine()<<"\n";
              errs()<<location.getCol()<<"\n";
              errs()<<*srcvalue<<"\n";
              errs()<<srcvalue->getValueID () <<"\n";
              int valueid=srcvalue->getValueID ();
              char *parm_srcname=NULL;
              parm_srcname=(char*)malloc(30*sizeof(char));  
              memset(parm_srcname,'\0',30);
                            
              
                  			if (valueid==56) //load
                  			{
                  				// get value of loadinst (second paremeter)
                          LoadInst *srcload=dyn_cast<LoadInst>(srcvalue);
                  				Value *val=srcload->getOperand(0);
                          

                            bound=deal_with_load(srcload,val,parm_srcname,F,inst_name);

                            

                  			}

                     else if ( valueid==58)//getElementPtr
                      {
                        int num=dyn_cast<Instruction>(srcvalue)->getNumOperands();
                                             
                        
                        bound=deal_with_gep(num,dyn_cast<Instruction>(srcvalue),parm_srcname,F,inst_name);
                        
                        
    
                      }


                      else if (srcvalue->getValueID ()==5) //struct type paramenter of function
                      {
                        // Instruction *inst=dyn_cast<Instruction>(srcvalue);
                        // errs()<<*inst<<"\n";
                        Constant *cons=dyn_cast<Constant>(srcvalue);
                        
                        Value *oprand1=cons->getOperand(0);
                        
                        if (PointerType  *consarray=dyn_cast<PointerType >(oprand1->getType()))
                        {                       
                          if (ArrayType * arrcons=dyn_cast<ArrayType>(consarray->getElementType ()))
                          {
                            bound=arrcons->getNumElements () ;                         
                          }
                          else
                          {
                            errs()<<*oprand1<<"5_continue1\n";
                            srcname="struct";
                            errs()<<srcname<<"\n";
                          }
                          
                        }else
                        {
                          errs()<<*oprand1<<"5_continue2\n";
                          errs()<<"5continue1\n";

                        }
                        
                      }
                      else if(srcvalue->getValueID ()==17) //basic type paremeter of function
                       
                      { srcname="struct";
                       errs()<<*srcvalue<<" 17\n";

                        errs()<<"3333\n";
                      }

                      else if (valueid==73)//bitcast
                      {
                        Value *srcbitcast=dyn_cast<Instruction>(srcvalue)->getOperand(0);
                        errs()<<*srcbitcast->getType()<<"\n";
                        if(PointerType *bitpoin=dyn_cast<PointerType>(srcbitcast->getType()))
                        {
                            
                            if (StructType *temptype=dyn_cast<StructType>(bitpoin->getElementType()))
                            {
                              
                              llvm::DataLayout* dl = new llvm::DataLayout(ins_iter->getModule ());
                                    bound = dl->getTypeStoreSize(temptype);
                                    errs()<<bound<<"\n";
                            
                  

                           
                            }else if (srcbitcast->getType()==PointerType::get(Type::getInt64Ty(F.getContext()), 0))
                            {
                              bound=8;
                              
                            }else
                            {
                              errs()<<*srcbitcast<<" 732_continue\n";
                             
                            }

                        }else
                        {
                          errs()<<*srcbitcast<<" 731_continue\n";
                        }
                        

                        
                      }


                      else if(valueid==79) //phi
                      {
                        errs()<<"start_deal_with_79\n";
                        Instruction *phiinst= dyn_cast<Instruction>(srcvalue);

                        int num=phiinst->getNumOperands();
                        std::vector<int> size_ret;
                        std::vector<char *> name_ret;
                        

                        deal_with_phi(num,phiinst,name_ret,size_ret,F,inst_name);
                        errs()<<"length"<<"\n";
                        for (auto inter=size_ret.begin();inter!=size_ret.end();inter++)
                        {
                          if (*inter>0)
                          {
                            bound=*inter;
                            break;
                          }
                          errs()<<*inter<<"\n";
                        }
                        errs()<<"output_string"<<"\n";
                        for (auto inter=name_ret.begin();inter!=name_ret.end();inter++)
                        {
                          if (!strcmp(*inter,"struct"))
                          {
                            srcname=*inter;
                            errs()<<srcname<<"\n";
                            break;
                          }
                          errs()<<*inter<<"\n";
                        }

                        
                      

                      }else if(valueid==80) //tail call
                      {
                        errs()<<*srcvalue<<" 80\n";
                        srcname="struct";
                        errs()<<srcname<<"\n";
                       }else
                       {
                        errs()<<"continue_others\n";
                       }

                       if (parm_srcname[0]!='\0')
                                {
                                  srcname=parm_srcname;
                                }
                                if (length==bound){
                                  length=-2;
                                  continue;
                                }

                                errs()<<srcname<<"\n";
                                errs()<<bound<<"\n";




          					   create_xml(xmlfilename.c_str(), type.c_str(),c_filename.c_str(),startline,endline,funname.c_str(),srcname.c_str(),srcline,incname.c_str(),len_three.c_str(),bound);
                       bound=0;

            }

					 }

					

					if (bb_iter->getName().str().substr(0,8)=="for.body")
					{
						 if (StoreInst *storeinst=dyn_cast<StoreInst>(ins_iter))
						{
							//src systax
							Value *storevalue=storeinst->getOperand(0);
              if(LoadInst *loadinst=dyn_cast<LoadInst>(storevalue))
              {
                Value *loadvalue=loadinst->getOperand(0);
                //errs()<<*loadvalue<<"\n";
                string strname=loadvalue->getName().str();
                if (strname.substr(0,7)=="arrayid")
                {
                  
                  type="for";
                  cout<<type<<endl;
                  Instruction *arrayinst=dyn_cast<Instruction>(loadvalue);
                  int num=arrayinst->getNumOperands();
                  Value *arrayval=arrayinst->getOperand(0);
                  Value *incval=arrayinst->getOperand(1);
                 
                  string arrayname;
                  
                  if ( LoadInst *loadinst=dyn_cast<LoadInst>(arrayval))
                  {
                    srcname=loadinst->getOperand(0)->getName().str();
                    
                  }else
                  {
                    srcname=arrayval->getName().str();

                  }
                  if (LoadInst *loadinc=dyn_cast<LoadInst>(incval))
                  {
                    incname= loadinc->getOperand(0)->getName().str();
                    len_three="";
               

                  create_xml(xmlfilename.c_str(),type.c_str(),c_filename.c_str(),startline,endline,funname.c_str(),srcname.c_str(),srcline,incname.c_str(),len_three.c_str(),bound);
                  bound=0;
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

char PProcessPass::ID = 0;
static RegisterPass<PProcessPass> X("process", "proprecess Analyse",
	false, false);
