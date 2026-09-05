from flask import Flask,render_template,request,jsonify,redirect,url_for
import mysql.connector
from datetime import datetime
app=Flask(__name__)

#get connection
def getconnetionwithDB():
    try:
        connection=mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysql',
        database='parking_management'
        )
        return connection
        
    except:
        
        return "Connection Failed"






def total_slots():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    total_slots_query='select count(*) from parking_slots;'
    cursor=connection.cursor()
    cursor.execute(total_slots_query)
    result=cursor.fetchone()
    total=result[0]
    cursor.close()
    connection.close()
    return total

def available_slots():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    available_slots_query="select count(*) from parking_slots where status='Available'"
    cursor=connection.cursor()
    cursor.execute(available_slots_query)
    result=cursor.fetchone()
    available=result[0]
    cursor.close()
    connection.close()
    return available
def occupied_slots():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    occupied_slots_query="select count(*) from parking_slots where status='Occupied'"
    cursor=connection.cursor()
    cursor.execute(occupied_slots_query)
    result=cursor.fetchone()
    occupied=result[0]
    cursor.close()
    connection.close()
    return occupied
    
def vehicle_type_overview():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    vehicle_type_overview_query="""
    select vehicle_type,count(*) as total_slots,
    sum(status='Available') as available_slots,
    sum(status='Occupied') as occupied_slots
    from parking_slots group by vehicle_type
    """
    cursor=connection.cursor(dictionary=True)
    cursor.execute(vehicle_type_overview_query)
    overview=cursor.fetchall()
    cursor.close()
    connection.close()
    return overview
    
def recent_records():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    recent_records_query='select * from parking_records order by entry_time desc limit 5'
    cursor=connection.cursor(dictionary=True)
    cursor.execute(recent_records_query)
    records=cursor.fetchall()
    cursor.close()
    connection.close()
    return records
    
    
    
    
    
    
@app.route('/')
def dashboard():
    total=total_slots()
    available=available_slots()
    occupied=occupied_slots()
    overview=vehicle_type_overview()
    records=recent_records()
    return render_template('dashboard.html',total_slots=total,available_slots=available,occupied_slots=occupied,vehicle_type_overview=overview,recent_records=records)

    
def selectall():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    cursor=connection.cursor(dictionary=True)
    cursor.execute('select * from parking_slots')
    all_records=cursor.fetchall()
    cursor.close()
    connection.close()
    return all_records
    
    
@app.route('/parkingslots')
def parkingslots():
    total=total_slots()
    available=available_slots()
    occupied=occupied_slots()
    overview=vehicle_type_overview()
    all_records=selectall()
    
    
    return render_template('parkingslots.html',total_slots=total,available_slots=available,occupied_slots=occupied,vehicle_type_overview=overview,selectall=all_records)


def getvehicle_type(vehicle_type):
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    
    cursor=connection.cursor(dictionary=True)
    getvehicle_type_query="""select id,slot_number from parking_slots where vehicle_type=%s and 
                                            status='Available'"""
    cursor.execute(getvehicle_type_query,(vehicle_type,))
    vehicle_type_records=cursor.fetchall()
    cursor.close()
    connection.close()
    return vehicle_type_records
    
def parkvehicle(vehicle_number,vehicle_type,slot_id):
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    cursor=connection.cursor()
    parkvehicle_query=("""insert into parking_records (vehicle_number,vehicle_type,slot_id)
                                     values(%s,%s,%s)
                                     """)
    cursor.execute(parkvehicle_query,(vehicle_number,vehicle_type,slot_id))
    update_query=("update parking_slots set status='Occupied' where id=%s")
    cursor.execute(update_query,(slot_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return "sucess"
    
    



@app.route('/vehicle_entry',methods=['GET','POST'])
def vehicle_entry():
    if request.method=='GET':
        return render_template('vehicleentry.html')
    if request.method=='POST':
        action=request.form.get('action')
        vehicle_type=request.form.get('vehicle_type')
        vehicle_number=request.form.get('vehicle_number')
        slot_id=request.form.get('slot')
        if action=='show_slots':
            
            slots=getvehicle_type(vehicle_type)
            return render_template('vehicleentry.html',slots=slots,vehicle_number=vehicle_number)
        elif action=='park':
            parkvehicle(vehicle_number,vehicle_type,slot_id)
            return render_template('dashboard.html')
            
def detilas(vehicle_number):
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    cursor=connection.cursor(dictionary=True)
    detilas_query="""select parking_records.* ,parking_slots.slot_number,parking_slots.status  from parking_records left join 
                                parking_slots on parking_records.slot_id=parking_slots.id where parking_records.vehicle_number=%s"""
    
    cursor.execute(detilas_query,(vehicle_number,))
    data=cursor.fetchall()
    cursor.close()
    connection.close()
    return data
    
@app.route('/vehicle_exit',methods=['GET','POST'])
def vehicle_exit():
    if request.method=='GET':
        return render_template('vehicleexit.html')
    if request.method=='POST':
        vehicle_number=request.form.get('vehicle_number')
        
        return redirect(url_for('vehicle_details',vehicle_number=vehicle_number))
    

@app.route('/vehicle_exit/vehicle_details')
def vehicle_details():
    vehicle_number=request.args.get('vehicle_number')
    data=detilas(vehicle_number)
    vehicle=data[0]
    entry_time=vehicle['entry_time']
    exit_time=datetime.now()
    duration=exit_time-entry_time
    hours=duration.total_seconds()/3600
    fee=round(hours*20)
    print("ENTRY TIME:", entry_time)
    print("EXIT TIME:", exit_time)
    print("DURATION:", duration)
    print("HOURS:", hours)
    print("FEE:", fee)
    return render_template('vehicledetails.html',vehicle=vehicle,fee=fee)


@app.route('/confirm_exit',methods=['POST'])
def confirm_exit():
    vehicle_number=request.form.get('vehicle_number')
    data=detilas(vehicle_number)
    print(data)
    vehicle=data[0]
    slot_id=vehicle['slot_id']
    entry_time=vehicle['entry_time']
    exit_time=datetime.now()
    duration=exit_time-entry_time
    hours=duration.total_seconds()/3600
    fee=round(hours*20)
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    cursor=connection.cursor()
    updated_record_query="""update parking_records set exit_time=%s,parking_fee=%s,status='Exited' where vehicle_number=%s"""
    cursor.execute(updated_record_query,( exit_time,fee,vehicle_number,))
    
    updated_parking_slot_query="""update parking_slots set status='Available' where id =%s"""
    cursor.execute(updated_parking_slot_query,(slot_id,))
    connection.commit()
    cursor.close()
    connection.close()
    
    
    return redirect(url_for('vehicle_exit'))
    


def get_history():
    connection=getconnetionwithDB()
    if connection=="Connection Failed":
        return False,"connection failed"
    cursor=connection.cursor(dictionary=True)
    get_history_query="""SELECT * FROM parking_records
                LEFT JOIN parking_slots ON parking_records.slot_id = parking_slots.id""" 
    cursor.execute(get_history_query)
    history=cursor.fetchall()
    cursor.close()
    connection.close()
    return history
    
      
    



@app.route('/viewhistory')
def viewhistory():
    history=get_history()
    return render_template('history.html',history=history)
    



@app.route('/')
def home():
    render_template('dashboard.html')
    
@app.route('/demo')
def demo():
    over=selectall()
    return jsonify(over)

if __name__=="__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
