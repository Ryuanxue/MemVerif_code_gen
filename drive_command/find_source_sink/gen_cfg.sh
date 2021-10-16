#!bin/bash
llfile=$(ls *.ll)
for file in $llfile
do

    opt -load libCFGPass.so -CFG $file

done

