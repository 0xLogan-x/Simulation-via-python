import simpy
import numpy as np
def car(env,parkingLot,entityname):
     waitingList=[]
     for i in range(1000):
        #capture parking lot
        r=parkingLot.request()
        requestedTime=env.now
        #print(entityname,'request parking lot at time:',env.now)
        yield r 
        waitingList=waitingList+[env.now-requestedTime]

        #parking for 5 hours
        #print (entityname,'start parking at time:', env.now)
        yield env.timeout(5)

        #release parking lot
        #print(entityname,"release parking lot at time:",env.now)
        parkingLot.release(r)
        
        #driving for 2 hours
        #print (entityname, 'car start driving at time:', env.now)
        yield env.timeout(2)
     print(entityname, 'waiting is:',np.mean(waitingList))


def car2(env,parkingLot,entityname):
     waitingList=[]
     for i in range(1000):
        #capture parking lot
        r=parkingLot.request()
        requestedTime=env.now
        #print(entityname,'request parking lot at time:',env.now)
        yield r 
        waitingList=waitingList+[env.now-requestedTime]

        #parking for 5 hours
        #print (entityname,'start parking at time:', env.now)
        yield env.timeout(4)

        #release parking lot
        #print(entityname,"release parking lot at time:",env.now)
        parkingLot.release(r)
        
        #driving for 2 hours
        #print (entityname, 'car start driving at time:', env.now)
        yield env.timeout(1)
    
     print('averge waiting time of',entityname,':',np.mean(waitingList))

     
env=simpy.Environment()
parkingLot=simpy.Resource(env, capacity=3)



env.process(car(env,parkingLot,'BMW'))
env.process(car(env,parkingLot,'BENZ'))
env.process(car(env,parkingLot,'FORD'))
env.process(car2(env,parkingLot,'FERRARI'))
env.process(car2(env,parkingLot,'LAMBOURGINI'))

env.run()


 
