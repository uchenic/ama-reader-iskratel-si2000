import configparser
from collections import defaultdict
import binascii
import io
import argparse
import os


def to_int(byte):
    return int.from_bytes(byte, byteorder='big')

def checksum(byte_seq):
    sign_bytes=[0,0]
    for i,x in enumerate(byte_seq):
        sign_bytes[i%2]+=x
    result = (sign_bytes[0]<<8)+sign_bytes[1]
    # print("{:0>4x}".format(result))
    return result.to_bytes((result.bit_length() + 7) // 8,byteorder="big")[-2:]

def logging_bytes_reader(f,length):
	global cs_log
	byte = f.read(length)
	cs_log.write(byte)
	return byte

def bcd_read(f,length,a):
	byte=logging_bytes_reader(f,(length+length%2)//2)
	stringr=''
	for b in byte:
		stringr+=''.join(str((b & (1 << i)) and 1) for i in reversed(range(8)))
	##print(stringr)
	#stringr=stringr[::-1]
	g=[]
	for i in range(0,(length)*4,4):
		if int(stringr[i:i+4],2) in range(10):
			g.append(str(int(stringr[i:i+4],2)))
		else:
			if int(stringr[i:i+4],2)==11:
				g.append('*')
			elif int(stringr[i:i+4],2)==12:
				g.append('#')
	a+=1

	return ''.join(g)

def R210(f):
	b=[]
	a=0
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))

def R211(f):
	b=[]
	a=0
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,4)
	a+=1
	#print(a,' ',to_int(byte))

def R212(f):
	b=[]
	a=0
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))

	byte=logging_bytes_reader(f,4)
	a+=1
	#print(a,' ',to_int(byte))




def R100(f):
	a=0
	#byte=logging_bytes_reader(f,1)
	#a+=1
	##print(a,' ',to_int(byte))
	global record
	a+=1
	byte=logging_bytes_reader(f,1)
	#print(a,' ',to_int(byte))
	gq=bcd_read(f,to_int(byte),a)
	#print(gq)
	record['PartN']=gq

def R101(f):
	global record
	a=0
	#byte=logging_bytes_reader(f,1)
	#a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	record['R101_F1']=to_int(byte)
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	gq=bcd_read(f,to_int(byte),a)
	record['R101_B_N']=gq

def R102(f):
	#byte=logging_bytes_reader(f,1)
	global record
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	b=list()
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
		b.append(to_int(byte))

	record['Start_DT']="20{0[0]}-{0[1]:0>2d}-{0[2]:0>2d}".format(list(b[:3]))
	record['Start_TT']="{0[0]:0>2d}:{0[1]:0>2d}:{0[2]:0>2d}".format(list(b[3:6]))

	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	record['R102_F1']=to_int(byte)

def R103(f):
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	b=[]
	for x in range(7):
		byte=logging_bytes_reader(f,1)
		a+=1
		#print(a,' ',to_int(byte))
		b.append(to_int(byte))

	record['End_DT']="20{0[0]}-{0[1]:0>2d}-{0[2]:0>2d}".format(b[:3])
	record['End_TT']="{0[0]:0>2d}:{0[1]:0>2d}:{0[2]:0>2d}".format(b[3:6])

	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	record['R103_F1']=to_int(byte)

def R104(f):
	#byte=logging_bytes_reader(f,1)
	global record
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,3)
	a=0
	a+=1
	#print(a,' ',to_int(byte))
	record['Pulses']=to_int(byte)

def R105(f):
	#byte=logging_bytes_reader(f,1)
	global record
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Bear_Serv']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Teleserv']=to_int(byte)

def R106(f):
	global record
	byte=logging_bytes_reader(f,1)

	a=1
	#print(a,' ',to_int(byte))
	record['R106_Suppl_Serv']=to_int(byte)


def R107(f):
	global record
	byte=logging_bytes_reader(f,1)
	a=1
	#print(a,' ',to_int(byte))
	record['R107_Suppl_Serv']=to_int(byte)

def R108(f):
	global record
	byte=logging_bytes_reader(f,1)

	a=1
	#print(a,' ',to_int(byte))
	record['Type_Inp']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['R108_Suppl_Serv']=to_int(byte)

def R109(f):
	global record
	byte=logging_bytes_reader(f,1)

	a=1
	q=to_int(byte)
	#print(a,' ',q)
	gq=bcd_read(f,q,a)
	#print(gq)
	record['R109_Seq']=gq

def R110(f):
	global record
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Origin_Cat']=to_int(byte)

def R111(f):
	global record
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Tariff_Dir']=to_int(byte)

def R112(f):
	global record
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)


	#print(a,' ',to_int(byte))
	record['Failure']=to_int(byte)

def R113(f):
	global record
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,2)

	a+=1
	#print(a,' ',to_int(byte))
	record['In_Tr_GrT']=to_int(byte)
	byte=logging_bytes_reader(f,2)
	a=0
	a+=1
	#print(a,' ',to_int(byte))
	record['In_TrT']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['In_Mod']=to_int(byte)
	byte=logging_bytes_reader(f,2)
	a=0
	a+=1
	#print(a,' ',to_int(byte))
	record['In_Port_ID']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['In_Chan_ID']=to_int(byte)

def R114(f):
	global record
	#byte=logging_bytes_reader(f,1)
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,2)

	a+=1
	#print(a,' ',to_int(byte))
	record['Out_Tr_GrT']=to_int(byte)
	byte=logging_bytes_reader(f,2)
	a=0
	a+=1
	#print(a,' ',to_int(byte))
	record['Out_TrT']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Out_Mod']=to_int(byte)
	byte=logging_bytes_reader(f,2)
	a=0
	a+=1
	#print(a,' ',to_int(byte))
	record['Out_Port_ID']=to_int(byte)
	byte=logging_bytes_reader(f,1)

	a+=1
	#print(a,' ',to_int(byte))
	record['Out_Chan_ID']=to_int(byte)

def R115(f):
	#byte=logging_bytes_reader(f,1)
	global record
	a=0
	a+=1
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,4)

	a+=1
	#print(a,' ',to_int(byte))
	record['Call_Durat']=to_int(byte)

def R116(f):
	global record,writelog,config,cs_log
	record['ResVer']=9
	#for x in record.keys():
	#	writelog.write(','+str(record[x]))
	#writelog.write('\n')

	a=1
	#byte=logging_bytes_reader(f,1)
	##print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	cs_log.seek(0,0)
	cs = checksum(cs_log.read())
	byte=f.read(2)
	if cs == byte:
		writelog.write(config['st']['StringFormat'].format_map(record)+'\n')
		record.clear()
		cs_log.close()
		cs_log = io.BytesIO(b"")
	else:
		raise Exception("checksum error")
	a+=1
	#print(a,' ',to_int(byte))

def R119(f):
	global record
	byte=logging_bytes_reader(f,1)
	a=1

	#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	q=to_int(byte)

	#print(a,' ',q)
	gq=bcd_read(f,q,a)
	#print(gq)


def R121(f):
	global record
	byte=logging_bytes_reader(f,1)
	a=1
	#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,2)
	a+=1
	#print(a,' ',to_int(byte))
	record['R_121_Course']=to_int(byte)
	byte = logging_bytes_reader(f,1)
	q="{:0>8b}".format(to_int(byte))
	#print(a,' ',int(q[1:3],2))
	#print(a,' ',int(q[4:],2))

def R122():
	byte=logging_bytes_reader(f,1)
	a=1
	#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))
	byte=logging_bytes_reader(f,1)
	a+=1
	#print(a,' ',to_int(byte))

def R200(f):
	#byte = logging_bytes_reader(f,1)
	a=0
	##print(a,' ',to_int(byte))
	global record

	a+=1
	byte = logging_bytes_reader(f,2)
	#print(a,' ',to_int(byte))
	a+=1
	byte = logging_bytes_reader(f,4)
	#print(a,' ',to_int(byte))
	record['NZ']=to_int(byte)
	a+=1
	byte = logging_bytes_reader(f,4)
	#print(a,' ',to_int(byte))
	record['Call_Proc_ID']=to_int(byte)
	a+=1
	byte = logging_bytes_reader(f,3)
	g="{:0>24b}".format(to_int(byte))
	F=list()
	F.extend(g[7::-1])
	F.extend(g[15:7:-1])
	F.extend(g[:15:-1])
	#print(a,' ',F,len(F))
	for i in range(len(F)):
		record['F'+str(i+1)]=F[i]
	a+=1
	byte = logging_bytes_reader(f,1)
	q="{:0>8b}".format(to_int(byte))
	#print(a,' ',int(q[:4],2))
	record['Sequence']=int(q[:4],2)

	#print(a,' ',int(q[4:],2))
	byte = logging_bytes_reader(f,1)
	a+=1
	q="{:0>8b}".format(to_int(byte))
	#print(a,' ',int(q[:3],2))

	#print(a,' ',int(q[3:],2))
	gq=bcd_read(f,int(q[3:],2)+int(q[:3],2),a)
	#print(gq)
	record['AMAOwner_N']=gq

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AMA files reader')
    parser.add_argument(
            'filename',
            help='file to process'
    )
    parser.add_argument(
            '--fileformat',
            nargs=1,
            #required=True,
            default='form.ini',
            help='output format string in file'
    )
    args = parser.parse_args()
    # print(args)
    filepath = os.path.abspath(args.filename)
    confpath = os.path.abspath(args.fileformat)
    a=1
    def const_factory(value):
    	return lambda: value


    record=defaultdict(const_factory(""))
    writelog=open("{}.txt".format(args.filename), "w")
    config=configparser.ConfigParser()
    config.read(confpath)
    cs_log = io.BytesIO(b"")

    with open(filepath, "rb") as f:

    	while True:

    		byte = logging_bytes_reader(f,1)
    		tt=to_int(byte)
    		#print(tt)
    		if tt not in [200,210,211,212] and tt not in range(100,129) :
    			byte = logging_bytes_reader(f,1)
    			#print(a,' ',to_int(byte))
    			break
    		locals()['R{}'.format(tt)](f)
