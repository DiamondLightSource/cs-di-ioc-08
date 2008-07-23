#!/dls_sw/tools/bin/python2.4

# retrieve the file information from a selected folder
# sort the files by last modified date/time and display in order newest file first
import os
import glob
import time,sys,re

def file_list(out_length,root,pm_day,pm_month,pm_year,pm_time):
    #root is the path to the files.
    #head of pm filename
    pm_head = 'bpm_postmortem-'
    date_file_list = []
    file_list = []
    if pm_day == '*':
        pm_day = '([0-9][0-9])'
    if pm_month == '*':
        pm_month = '([0-9][0-9])'
    if pm_year == '*':
        pm_year = '([0-9][0-9][0-9][0-9])'
    if pm_time == '*':
        pm_time = '([0-9][0-9]:[0-9][0-9]:[0-9][0-9])'
   #constructing search value
    search_string= str(root) + pm_head + str(pm_year) + '-' + str(pm_month) + '-' + str(pm_day) + 'T' + str(pm_time) + '.mat'
    val = re.compile(search_string)
    for folder in glob.glob(root):
#        print "folder =", folder
     # select the type of file, for instance *.mat or all files *.*
        for file in glob.glob(folder + '/' +pm_head +'*.mat'):
            if val.match(file):
                # get date from filename
                offset = len(root) + len(pm_head)
                pm_date = file[offset:-4]
                pm_date = time.strptime(pm_date,"%Y-%m-%dT%H:%M:%S")
                # create list of tuples ready for sorting by date
                date_file_tuple = (pm_date, file)
                date_file_list.append(date_file_tuple)
                file_list.append(file)
        

    date_file_list.sort()
    date_file_list.reverse()  # newest mod date now first
    # Changing from 1 list of 2D tupples to 2 tupples the length of the original list
    names = zip(*date_file_list)[1]
    file_list = names[0:int(out_length)]
    return file_list


# save task
if __name__ == "__main__":
    #list_of_files, list_of_timestamps =  file_list(*sys.argv[1:])
    #print list_of_files
    #print list_of_timestamps
    list_of_files =  file_list(*sys.argv[1:])
    print list_of_files
