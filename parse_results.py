
import argparse

def read_file(log="./timeNormalWrite3_7MB.txt"):

    f = open(log, "r")
    measurements = f.readlines()
    b_path_mean = get_B_path_mean(measurements)
    #a_path_mean = get_A_path_mean(measurements)
    #recovery_time_mean = get_mean_recovery_time(measurements)

    #print "==== A PATH MEAN ====\n", a_path_mean, "\n===="
    print "==== B PATH MEAN ====\n", b_path_mean, "\n===="

    #print "==== RECOVERY TIME MEAN ====\n", recovery_time_mean, "\n===="

def get_A_path_mean(measurements):
    return get_generic_path_mean(measurements, "Write")


def get_B_path_mean(measurements):
    return get_generic_path_mean(measurements, "Read")

"""
def get_mean_recovery_time(measurements):
    prev = ["","","","","",""]
    result = list()
    for m in measurements:
        raw_measure = m.split(" ")
        if prev[0] == "" and not len(raw_measure) == 6:
            continue
        if len(raw_measure) == 6:
            prev = raw_measure
            continue
        if raw_measure[1] == "DPID:00-00-00-00-00-03" and not prev[0] == "":
            result.append(calculate_delay(prev[5], raw_measure[3]))
            prev = ["","","","","",""]
    return get_mean(result)
"""
def get_generic_path_mean(measurements, path_id):
    prev = ["","","","","",]
    result = list()

    for m in measurements:
        print "m: ", m
        raw_measure = m.split(" ")
        print "len(raw_measure): ", len(raw_measure)
        if not len(raw_measure) == 6:
            continue
        if not path_id in raw_measure[0]:
            continue
        dpid = raw_measure[1]
        print "dpid: ", dpid
        #if dpid == prev[1] or prev[1] == "" or dpid == "DPID:00-00-00-00-00-02":
        if dpid == prev[1] or prev[1] == "" or dpid == "start":
            prev = raw_measure
            continue
        #result.append(calculate_delay(prev[3],raw_measure[3]))
        result.append(calculate_delay(prev[5], raw_measure[5]))
    return get_mean(result)
                
def calculate_delay(prev_time, current_time):
    start_time = format_time(prev_time)
    end_time = format_time(current_time)
    return end_time - start_time

def format_time(time_str):
    split = time_str.split(":")
    print "split: ", split
    minutes = split[0]
    seconds = split[1].split(".")[0]
    millis = split[1].split(".")[1]
    formatted_time = int(minutes) * 60000 + int(seconds) * 1000 + int(millis)
    return formatted_time
    
def get_mean(data):
    print "data: ", data
    return sum(data)/len(data)        


parser = argparse.ArgumentParser(description='Measurer results parser')
parser.add_argument('--file', '-f', dest='time_log', default=None,
                    help='File path, e.g., pox/time_log.txt', metavar='FILE')
args = parser.parse_args()
print "FILE: ", args, "\n"
log_file = args.time_log

print "*********************************************************************"
print "-= ", log_file, " =-"
print "*********************************************************************"            
read_file(log_file)
print "*********************************************************************"

"""
print "-= SOFT_LOG RESULTS =-"
print "*********************************************************************"            
read_file()
print "*********************************************************************"
"""
