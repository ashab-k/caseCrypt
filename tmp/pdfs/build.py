import re,io,pdfplumber
from pypdf import PdfReader,PdfWriter
from pypdf.generic import ContentStream
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
SRC='/Users/ashabkhan/Downloads/azure report11 (1) (1).pdf'
OUT='output/pdf/Industrial_Equipment_Predictive_Maintenance_Mohammad_Ashab.pdf'
for k,f in [('R','Times New Roman.ttf'),('B','Times New Roman Bold.ttf'),('I','Times New Roman Italic.ttf')]:pdfmetrics.registerFont(TTFont(k,'/System/Library/Fonts/Supplemental/'+f))
repls=[('Remote Patient Health Monitoring','Industrial Equipment Predictive Maintenance'),('REMOTE PATIENT HEALTH','INDUSTRIAL EQUIPMENT'),('MONITORING "','PREDICTIVE MAINTENANCE"'),('remote patient monitoring','equipment condition monitoring'),('Remote Patient Monitoring','Predictive Maintenance'),('patient health measurements','equipment operating measurements'),('patient health parameters','equipment operating parameters'),('patient health data','equipment telemetry data'),('patient health information','equipment condition information'),('patient health readings','equipment sensor readings'),('patient health status','equipment operating status'),('patient health','equipment condition'),('patients\' health conditions','equipment operating conditions'),("patients' health",'equipment condition'),("patient's health condition",'machine operating condition'),("patient's vital signs",'machine operating parameters'),("patients' vital signs",'equipment sensor readings'),('healthcare providers or caregivers','maintenance engineers or operators'),('healthcare providers and caregivers','maintenance engineers and operators'),('healthcare providers','maintenance engineers'),('healthcare professionals','maintenance engineers'),('caregivers','operators'),('medical sensors or wearable devices','industrial sensors or PLC devices'),('wearable medical devices','industrial sensor devices'),('Wearable devices and medical sensors','Industrial sensors and PLC devices'),('wearable devices','industrial devices'),('medical sensors','industrial sensors'),('medical devices','industrial devices'),('vital health parameters','machine operating parameters'),('vital parameters','operating parameters'),('vital sign measurements','sensor measurements'),('vital sign','sensor'),('heart rate, body temperature, blood oxygen saturation (SpO₂), and blood pressure','temperature, vibration, pressure, and rotational speed'),('heart rate, body temperature, blood oxygen level (SpO₂), and blood pressure','temperature, vibration, pressure, and rotational speed'),('heart rate, body temperature, and blood oxygen saturation','temperature, vibration, and pressure'),('heart rate, body temperature, and SpO₂','temperature, vibration, and pressure'),('heart rate, body temperature, SpO₂, blood pressure','temperature, vibration, pressure, rotational speed'),('heart rate','vibration'),('body temperature','bearing temperature'),('blood oxygen saturation (SpO₂)','pressure'),('blood oxygen level (SpO₂)','pressure'),('blood pressure','rotational speed'),('SpO₂','pressure'),('health abnormalities','equipment anomalies'),('abnormal health conditions','abnormal equipment conditions'),('health conditions','equipment conditions'),('health measurements','sensor measurements'),('health readings','sensor readings'),('health parameters','operating parameters'),('health trends','equipment trends'),('health risks','failure risks'),('health risk','failure risk'),('health datasets','equipment datasets'),('health records','maintenance records'),('health data','equipment data'),('health status','equipment status'),('health information','equipment information'),('health concerns','equipment faults'),('Health Sensors','Industrial Sensors'),('Health Monitoring','Condition Monitoring'),('Healthcare IoT','Industrial IoT'),('Healthcare','Manufacturing'),('healthcare','maintenance'),('Patient Health','Equipment Condition'),('Patient','Equipment'),('patient','equipment'),('patients','machines'),('medical intervention','maintenance intervention'),('medical attention','maintenance attention'),('medical complications','equipment failures'),('medical assessment','engineering assessment'),('medical diagnosis or treatment','inspection or servicing'),('clinical diagnosis','engineering inspection'),('clinical assessment','engineering inspection'),('clinical validation','operational validation'),('clinical','operational'),('medical','industrial'),('treatment','repair'),('hospital visits','machine inspections'),('hospitals','factory sites'),('hospital','factory'),('elderly equipment and individuals with chronic illnesses','aging machines and assets under continuous operation'),('elderly machines and individuals with chronic illnesses','aging machines and assets under continuous operation'),('individuals with chronic illnesses','assets under continuous operation'),('routine checkups','scheduled inspections'),('periodic checkups','periodic inspections'),('personalized maintenance recommendations','condition-based maintenance recommendations'),('personalized maintenance decisions','condition-based maintenance decisions'),('rural or underserved areas','remote or distributed facilities')]
def transform(t):
 for a,b in repls:t=t.replace(a,b)
 t=t.replace('equipments','machines').replace('elderly machines','aging machines').replace('machines living in','machines operating in').replace('require machines to visit factory sites for scheduled inspections','require manual inspection of machines during scheduled shutdowns').replace('blood oxygen level (pressure)','pressure').replace('blood oxygen saturation (pressure)','pressure').replace('health measurement','sensor measurement').replace('health thresholds','equipment thresholds').replace('health monitoring','condition monitoring').replace('Medical sensors','Industrial sensors').replace('maintenance provider or caregiver','maintenance engineer or operator').replace('Manufacturing providers','Maintenance engineers').replace('Timely Health Alerts','Timely Maintenance Alerts').replace('transmitted the Azure cloud','transmitted to the Azure cloud').replace('Remote Equipment Condition Monitoring','Industrial Equipment Predictive Maintenance')
 t=t.replace('blood oxygen level (pressure)','pressure').replace('oxygen level (pressure), and rotational speed.','and rotational speed.').replace('bearing temperature, blood','bearing temperature, pressure,').replace("machines' machine operating parameters",'machine operating parameters')
 return t

def font(l):
 ch=l['chars'];f=max(ch,key=lambda x:x['size']);name=f['fontname'];return ('B' if 'Bold' in name else 'I' if 'Italic' in name else 'R'),round(f['size'],2)
def draw(c,t,x,top,f='R',size=12):
 c.setFont(f,size);c.drawString(x,792-top-size*.82,t)
def wrap(t,f,s,w):
 lines=[];line=''
 for word in t.split():
  test=(line+' '+word).strip()
  if pdfmetrics.stringWidth(test,f,s)>w and line:lines.append(line);line=word
  else:line=test
 if line:lines.append(line)
 return lines

def diagram(c,top,workflow=False):
 labels=[('Industrial Sensors','Temp | Vibration','Pressure | RPM'),('IoT Gateway','Timestamp + JSON','Secure telemetry'),('Azure IoT Hub','Device ingestion','Message routing'),('Azure Functions','Validate + classify','Threshold rules'),('Data Storage','Data Explorer','Blob archive'),('Power BI','Trends + status','Maintenance view')]
 x0=69;w=72;gap=8;y=792-top-74
 for i,ls in enumerate(labels):
  x=x0+i*(w+gap);c.setFillColor(HexColor(['#e9f4fc','#edf6e8','#e9f4fc','#fff5dd','#eef0fc','#e4f5f5'][i]));c.setStrokeColor(HexColor('#6d97b1'));c.rect(x,y,w,74,fill=1)
  c.setFillColor(HexColor('#111111'))
  for j,l in enumerate(ls):c.setFont('B' if j==0 else 'R',7.3);c.drawCentredString(x+w/2,y+55-j*16,l)
  if i<5:c.line(x+w,y+37,x+w+gap,y+37)
 for i,(a,b) in enumerate([('Logic Apps','Notify engineers'),('Maintenance Team','Inspect and service'),('Machine Learning','Future failure model')]):
  x=250+i*83;c.setFillColor(HexColor('#fff0f1' if i==0 else '#eef5f9'));c.rect(x,y-82,75,57,fill=1);c.setFillColor(HexColor('#111111'));c.setFont('B',8);c.drawCentredString(x+37.5,y-43,a);c.setFont('R',7.5);c.drawCentredString(x+37.5,y-60,b)
 c.line(325,y,325,y-25)

reader=PdfReader(SRC);writer=PdfWriter();source=pdfplumber.open(SRC)
for idx,page in enumerate(reader.pages):
 # Keep borders, logo and table rules; remove all source text and topic diagrams.
 cs=ContentStream(page.get_contents(),reader);ops=[];inside=False
 for args,op in cs.operations:
  if op==b'BT':inside=True
  if not inside and not(idx in [7,12] and op==b'Do'):ops.append((args,op))
  if op==b'ET':inside=False
 cs.operations=ops;page.replace_contents(cs)
 buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(612,792));lines=source.pages[idx].extract_text_lines(return_chars=True)
 if idx==0:
  for l in lines:
   f,s=font(l);t=l['text']
   if t.startswith('MANYA'):draw(c,'MOHAMMAD ASHAB',157.3,l['top'],f,s);draw(c,'1DS23IC027',373,l['top'],f,s);continue
   if t=='NAME USN':draw(c,'NAME',192.8,l['top'],f,s);draw(c,'USN',389,l['top'],f,s);continue
   t=transform(t);x=l['x0']
   if l['top'] in []:pass
   if 280<l['top']<325:x=(612-pdfmetrics.stringWidth(t,f,s))/2
   draw(c,t,x,l['top'],f,s)
 elif idx==1:
  for l in lines:
   if l['top']<100 or l['top']>725:
    f,z=font(l)
    if l['text'].startswith('S. No.'):
     draw(c,'S. No.',70,l['top'],'B',12);draw(c,'Contents',280,l['top'],'B',12);draw(c,'Page No.',535,l['top'],'B',12)
    else:draw(c,l['text'],l['x0'],l['top'],f,z)
  rows=[('Abstract',4),('Introduction',5),('Problem Statement',6),('Objectives',7),('Proposed System Architecture',8),('Relevant Azure Services',10),('Implementation Steps',13),('Sample IoT Telemetry Data',15),('Expected Outcomes',17),('Conclusion',18),('References',19)]
  rr=[l for l in lines if re.match(r'^\d+\.',l['text'])]
  for j,((title,num),l) in enumerate(zip(rows,rr)):
   top=l['top'];draw(c,str(j+1)+'.',70,top);draw(c,title,215,top);draw(c,str(num),545,top)
 elif idx==2:
  for l in lines:
   if l['text'] in ['LIST OF FIGURES','LIST OF TABLES'] or l['top']>725 or l['text'].startswith(('Figure No.','Table No.')):
    f,z=font(l)
    if l['text'].startswith(('Figure No.','Table No.')):
     draw(c,'Figure No.' if l['text'].startswith('Figure') else 'Table No.',42,l['top'],'B',11.4);draw(c,'Title',300,l['top'],'B',11.4);draw(c,'Page No.',541,l['top'],'B',11.4)
    else:draw(c,l['text'],l['x0'],l['top'],f,z)
  rr=[l for l in lines if l['text'].startswith('Figure 1') or l['text'].startswith('Figure 2') or l['text'].startswith('Table 1')]
  for l,num,title,pg in zip(rr,['Figure 1','Figure 2','Table 1'],['Proposed System Architecture of the Azure IoT-Based Industrial Equipment Predictive Maintenance System','Implementation Workflow of the Azure IoT-Based Industrial Equipment Predictive Maintenance System','Sample IoT Telemetry Data for Industrial Equipment Predictive Maintenance'],['8','13','15-16']):
   draw(c,num,44,l['top'],'R',10.2)
   for j,txt in enumerate(wrap(title,'R',10.2,405)):draw(c,txt,121,l['top']-8+j*13,'R',10.2)
   draw(c,pg,552,l['top'],'R',10.2)
 elif idx==14:
  for l in lines:
   if l['top']<110 or l['top']>720: f,s=font(l);draw(c,l['text'],l['x0'],l['top'],f,s)
  xs=[18,104,204,310,394,511];heads=['Timestamp','Temperature (°C)','Vibration (mm/s)','Pressure (bar)','Speed (RPM)','Machine Status']
  for x,t in zip(xs,heads):draw(c,t,x,122,'B',9)
  temps=[55,56,57,58,59,60,67,70,73,76,83,87,90,85,72,60,57,55]
  vib=[1.2,1.3,1.4,1.5,1.6,1.7,3.1,3.5,4,4.3,5.2,5.6,6,5.4,3.8,1.8,1.4,1.2]
  for j in range(18):
   vals=[f'{10+j//12:02}:{j%12*5:02} AM',str(temps[j]),str(vib[j]),str(round(5+j*.04,2)),str(1500+j*3),'Critical' if 10<=j<=13 else 'Warning' if 6<=j<=14 else 'Normal']
   for x,t in zip(xs,vals):draw(c,t,x,141.3+j*19.53,'R',9)
  t='The overall machine status follows the most severe detected condition. For this illustrative motor, temperature of 65 to below 80 °C or vibration of 3 to below 5 mm/s indicates Warning. Temperature of 80 °C or above or vibration of 5 mm/s or above indicates Critical. Otherwise, status is Normal. Pressure and speed provide operating context. These example limits require validation against the manufacturer specifications and the actual machine load. The readings are simulated and do not establish predictive accuracy or remaining useful life.'
  for j,t in enumerate(wrap(t,'R',12,576)):draw(c,t,18,574.8+j*20.7)
 elif idx==15:
  texts=['Sample JSON Telemetry','The IoT device or simulator sends timestamped equipment readings in JSON format to Azure IoT Hub.','{','  "deviceId": "Motor_01",','  "timestamp": "2026-10-27T11:00:00+05:30",','  "temperature": 90,','  "vibrationRms": 6.0,','  "pressureBar": 5.48,','  "speedRpm": 1536,','  "units": {','    "temperature": "C", "vibrationRms": "mm/s"','  },','  "status": "Critical"','}']
  for j,t in enumerate(texts):draw(c,t,18,54.8+j*20.7,'B' if j==0 else 'R',12)
  t='Azure Functions derives equipment status from the configured rules; a device-provided status is checked before use. A threshold crossing triggers the maintenance notification workflow. Historical telemetry supports trend analysis, inspection planning, and later model training. A predictive model requires labeled failure histories, time-based validation, and evaluation of false alerts and useful warning lead time. The example demonstrates condition monitoring; it does not claim a validated failure prediction.'
  for j,t in enumerate(wrap(t,'R',12,576)):draw(c,t,18,365.9+j*20.7)
  draw(c,'16',301.5,731.6)
 else:
  groups=[]
  for l in lines:
   f,s=font(l)
   # retain independent rows for contents, lists, references and headings
   newitem=bool(re.match(r'^\d+\. ',l['text']))
   separate=idx in [1,2,18] or s>13 or l['text'].startswith(('•','Step ','Role in','Azure ','Microsoft ','Working of','Description of','Evaluation Criteria')) or l['top']>725
   if groups and not newitem and not separate and not groups[-1]['sep'] and font(groups[-1]['ls'][-1])==(f,s) and l['top']-groups[-1]['ls'][-1]['top']<23:
    groups[-1]['ls'].append(l)
   else:groups.append({'ls':[l],'sep':separate})
  for g in groups:
   ls=g['ls'];f,s=font(ls[0]);t=transform(' '.join(l['text'] for l in ls));x=ls[0]['x0'];top=ls[0]['top']
   if idx==7 and t.startswith('1. Sensing Layer:'):t='1. Sensing Layer: Industrial sensors measure temperature, vibration, pressure, and rotational speed. Timestamped measurements reveal changes in machine operation. Sensor placement, calibration, sampling rate, and load conditions must be recorded so that operating trends can be compared reliably.'
   if idx==1:
    nums={'Proposed System Architecture':'8','Relevant Azure Services':'10','Implementation Steps':'13','Sample IoT Telemetry Data':'15'}
    for name,n in nums.items():
     if name in t:t=re.sub(r'\d+$',n,t)
   if idx==2:t=t.replace('Figure 2 Figure 2:','Figure 2').replace('15-16','15')
   if len(ls)==1 and (idx in [1,2,18] or s>13 or top>725):
    # Preserve tabular columns by using original large character gaps.
    if idx in [1,2] and not ('Predictive' in t):
     segments=[];run=[];last=None
     for ch in ls[0]['chars']:
      if last and ch['x0']-last['x1']>15:
       if run:segments.append(run);run=[]
      run.append(ch);last=ch
     if run:segments.append(run)
     if len(segments)>1:
      for seg in segments:draw(c,transform(''.join(z['text'] for z in seg)),seg[0]['x0'],top,f,s)
      continue
    w=min(576,596-x);sz=s
    while pdfmetrics.stringWidth(t,f,sz)>w:sz-=.1
    draw(c,t,x,top,f,sz);continue
   w=(550-x if idx not in [12,13] else 590-x)
   if idx in [1,2,18]:w=590-x
   out=wrap(t,f,s,w);leading=(ls[-1]['top']-top)/(len(ls)-1) if len(ls)>1 else 20.7
   # Keep each paragraph within its original vertical allocation.
   if len(out)>len(ls):
    while len(out)>len(ls) and s>10.5:s-=.15;out=wrap(t,f,s,w)
    if len(out)>len(ls):leading=min(leading,(max(len(ls),1)*20.7)/len(out))
   for j,txt in enumerate(out):draw(c,txt,x,top+j*leading,f,s)
  if idx==7:diagram(c,355)
  if idx==12:diagram(c,280,True)
 c.save();buf.seek(0);page.merge_page(PdfReader(buf).pages[0]);writer.add_page(page)
writer.write(OUT)
print(OUT)
