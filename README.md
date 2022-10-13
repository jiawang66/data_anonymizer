# Data Anonymizer 

Anonymize DICOM files and Siemens MRI raw data files (.dat).

1) Anonymize the dicom file based on the matlab function "anonymizeDICOMs.m"

2) Anonymize the .dat file based on a python tool "twixtools". The script will call the python file "dat_anonymizer.py" to execute the anonymization of .dat file. You should set the path of python complier in file "setData_anonymize.m". About "twixtools", please refer to <https://github.com/pehses/twixtools>.

