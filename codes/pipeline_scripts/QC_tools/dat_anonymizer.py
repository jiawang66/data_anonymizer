import twixtools
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse


# Create the parser
parser = argparse.ArgumentParser()

# Add an argument
parser.add_argument('--dir', type=str, required=True)
parser.add_argument('--filename', type=str, required=True)
parser.add_argument('--targetname', type=str, required=True)

anony_name = 'xxxxxxxxxxxx'
anony_birthday = 'xxxxxxxx'
anony_ID = 'xxxxxxxxxxxxx'
anony_name_meas = '<Visible> true             xxxxxxxxxxxx'
anony_birthday_meas = '<Visible> true             xxxxxxxx'

if __name__ == '__main__':
    # Parse the argument
    args = parser.parse_args()
    example_dir = args.dir
    filename = args.filename
    filename_new = args.targetname
    filepath = os.path.join(example_dir, filename)
    # filepath_new = os.path.join(example_dir, filename_new)
    filepath_new = filename_new
    # parse the twix file
    twix = twixtools.read_twix(filepath)

    # twix is a list of measurements:
    print('\nnumber of separate scans (multi-raid):', len(twix))
    
    is_change = 0
    
    for i in range(len(twix)):
        if twix[i]['hdr']['Config']['tPatientName'] != anony_name:
            print(twix[i]['hdr']['Config']['tPatientName'])
            print('Anonymizing Config PatientName...')
            twix[i]['hdr']['Config']['tPatientName'] = anony_name
            is_change = 1

        if twix[i]['hdr']['Config']['PatientID'] != anony_ID:
            print(twix[i]['hdr']['Config']['PatientID'])
            print('Anonymizing Config PatientID...')
            twix[i]['hdr']['Config']['PatientID'] = anony_ID
            is_change = 1

        if twix[i]['hdr']['Config']['PatientBirthDay'] != anony_birthday:
            print(twix[i]['hdr']['Config']['PatientBirthDay'])
            print('Anonymizing Config PatientBirthDay...')
            twix[i]['hdr']['Config']['PatientBirthDay'] = anony_birthday
            is_change = 1

        if twix[i]['hdr']['Config']['PatientName'] != anony_name:
            print(twix[i]['hdr']['Config']['PatientName'])
            print('Anonymizing Config PatientName...')
            twix[i]['hdr']['Config']['PatientName'] = anony_name
            is_change = 1

        if twix[i]['hdr']['Dicom']['tPatientName'] != anony_name:
            print(twix[i]['hdr']['Dicom']['tPatientName'])
            print('Anonymizing Dicom PatientName...')
            twix[i]['hdr']['Dicom']['tPatientName'] = anony_name
            is_change = 1

        if twix[0]['hdr']['Meas']['tPatientName'] != anony_name:
            print(twix[0]['hdr']['Meas']['tPatientName'])
            print('Anonymizing Meas PatientName...')
            twix[0]['hdr']['Meas']['tPatientName'] = anony_name
            is_change = 1

        if twix[i]['hdr']['Meas']['PatientName'] != anony_name_meas:
            print(twix[i]['hdr']['Meas']['PatientName'])
            print('Anonymizing Meas PatientName...')
            twix[i]['hdr']['Meas']['PatientName'] = anony_name_meas
            is_change = 1

        if twix[i]['hdr']['Meas']['PatientID'] != anony_ID:
            print(twix[i]['hdr']['Meas']['PatientID'])
            print('Anonymizing Meas PatientID...')
            twix[i]['hdr']['Meas']['PatientID'] = anony_ID
            is_change = 1

        if twix[i]['hdr']['Meas']['PatientBirthDay'] != anony_birthday_meas:
            print(twix[i]['hdr']['Meas']['PatientBirthDay'])
            print('Anonymizing Meas PatientBirthDay...')
            twix[i]['hdr']['Meas']['PatientBirthDay'] = anony_birthday_meas
            is_change = 1
   
    if is_change ==1:
        twixtools.write_twix(twix, filepath_new)
        print('Anonymized dat file saved.')
    else:
        print('The dat file has already anonymized.')
