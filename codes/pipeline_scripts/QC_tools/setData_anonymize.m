% Data Anonymizer
% including dicom file and .dat file acquired from Siemens MR.
% 
% 1) Anonymize the dicom file based on the matlab function "anonymizeDICOMs"
% 2) Anonymize the .dat file based on a python tool "twixtools-master".
%    The script will call the python file "dat_anonymizer.py" to execute
%    the anonymization of .dat file.
%
% Jia Wang @ SJTU
% 13 Oct 2022
%
% Modified (12 NOV 2022)
% Fix the path name in `cmd` with space.

clc, clear, close all

%% initialization

% ----- set path ----------------------------------------------------------
parentFolderName = 'Epilepsy_20221112';
dataDir = fullfile('/data/share', parentFolderName);            % path of the data
processFolder = fullfile('/data/share/temp', parentFolderName); % path of the data after anony

pythonPath = '/home/jiawong/anaconda3/bin/python3';             % path of the python complier
pyfilePath = 'dat_anonymizer.py';                               % path of the python file

% ----- set the parameters for data transfer ------------------------------
host = '120.0.0.1';  % IP host
port = '22';         % Port number
user = 'username';   % username
passwd = 'passwd';   % Password
toDir = '/data/';    % Folder on the target server to save the data

%% set the path

if ~exist(processFolder, 'dir'); mkdir(processFolder); end

dataIDList = dir(dataDir);
dataIDList = dataIDList(~ismember({dataIDList.name},{'.','..'}));
dataIDList = {dataIDList.name}';

%% anonymize the dicom

for idx =1:length(dataIDList)
    % data information
    dataIDFullName     = dataIDList{idx};
    dataID             = strsplit(dataIDFullName, '_');
    dataID             = dataID{1};
    dataPath           = fullfile(dataDir, dataIDFullName);
    
    DataPathDir        = dir(fullfile(dataPath,'*'));
    DataScanName       = {DataPathDir.name}'; 

    for i = 3:length(DataScanName)
        scanName = DataScanName{i};
        scanSplits = strsplit(scanName,'_');
        scanType = scanSplits{end};
        scanDir = fullfile(dataPath,scanName,filesep);
        
        % path to save data
        tarName = sprintf('%s_%s', dataID, scanType);
        tarDir = fullfile(processFolder, dataID, tarName);
        if ~exist(tarDir,'dir'); mkdir(tarDir); end
        
        % start anonymizer
        if strcmpi(scanType, 'SPICE') == 0 && strcmpi(scanType, 'MRS') == 0
            % ----- DICOM file --------------------------------------------
            copyfile(scanDir, tarDir);
            anonymizeDICOMs(tarDir, sprintf('anon_%s',tarName),1);
        else
            % ----- .dat file ---------------------------------------------
            SpiceDataPathDir = dir(scanDir);
            SpiceDataScanName = {SpiceDataPathDir.name}';
            
            for j = 3:length(SpiceDataScanName)
                filename = SpiceDataScanName{j};
                renamefile = fullfile(tarDir,['anony_',filename(strfind(filename,'meas'):end)]);

                cmd = sprintf('''%s'' ''%s'' --dir ''%s'' --filename ''%s'' --targetname ''%s''', ...
                                pythonPath, ...
                                pyfilePath, ...
                                scanDir, ...
                                filename, ...
                                renamefile);
                fprintf('Anonymize .dat of %s/%s...', dataID, filename)
                unix(cmd)
                fprintf('done.\n')
            end
        end
        
    end
end

%% transfer data

% for idx =1:length(dataIDList)
%     % data information
%     dataIDFullName     = dataIDList{idx};
%     dataID             = strsplit(dataIDFullName, '_');
%     dataID             = dataID{1};
%     
%     subDir = fullfile(processFolder, dataID);
%     tarDir = fullfile(toDir, parentFolderName, dataID);
%     
%     cmd = sprintf('sshpass -p %s scp -r -P %s ''%s'' %s@%s:''%s''', passwd, port, subDir, user, host, tarDir);
%     fprintf('Start transfer %s...', dataID)
%     unix(cmd)
%     fprintf('done.\n')
%     
% end

cmd = sprintf('sshpass -p %s scp -r -P %s ''%s'' %s@%s:''%s''', passwd, port, processFolder, user, host, toDir);
fprintf('Start transfer ...')
unix(cmd)
fprintf('done.\n')
