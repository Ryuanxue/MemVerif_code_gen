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
#include "llvm/Support/CommandLine.h"
#include <stdio.h>

#include <iostream>
#include "tinyxml2.h"

#include "llvm/Support/Casting.h"

using namespace llvm;
using namespace std;
using namespace tinyxml2;

static cl::opt<std::string> getxmlfilename("xmlfile", cl::desc("Specify function name for mypass"), cl::value_desc("xmlfilename"));

namespace 
{
	struct Find_Sink_Pass : public FunctionPass 
	{
		static char ID;
		std::string str;
	
		Find_Sink_Pass() : FunctionPass(ID)
		{
		}

    void create_xml(const char* xmlPath,const char* Dir,
                const char* c_filename,
                int linenum
                )
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
      element->SetAttribute("Dir", Dir);
      element->SetAttribute("c_filename",c_filename);
      element->SetAttribute("linenum",linenum);
      
      doc.SaveFile(xmlPath);
    }

    bool runOnFunction(Function &F) override
    {
       string xmlfilename;
            for(auto &e : getxmlfilename) 
            {
                string s(1,e);
                xmlfilename.append(s);         
            }

    	for (auto bb_iter=F.begin();bb_iter!=F.end();++bb_iter)
		  {
  			for (auto ins_iter=bb_iter->begin();ins_iter!=bb_iter->end();++ins_iter)
  			{
          if (CallInst *call= dyn_cast<CallInst>(ins_iter))
              {
                string name;
                if (Function *fun=call->getCalledFunction())
                  {
                    name=fun->getName().str();
                    if (name=="BIO_write")
                    {
                      if (DILocation *Loc = ins_iter->getDebugLoc())
                {
                                            
                  
                  int Line = Loc->getLine();
                  string File = Loc->getFilename().str();
                  string Dir = Loc->getDirectory().str();
                  errs()<<Dir<<":"<<File<<":"<<Line<<"\n";
                  create_xml(xmlfilename.c_str(),Dir.c_str(), File.c_str(),Line);

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

char Find_Sink_Pass::ID = 0;
static RegisterPass<Find_Sink_Pass> X("find-sink", "proprecess Analyse",
	false, false);


