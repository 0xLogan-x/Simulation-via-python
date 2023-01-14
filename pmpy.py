import simpy
import numpy as np
import pandas as pd
import bisect

'''
pmpy Project Management with Python
'''

'''
*****************************************
*****Entity Class*******************
*****************************************
'''
def switchDic(dic):
    '''
    siwtch key and value in a dictionary
    '''
    newdic={}
    for key in dic:
        newdic[dic[key]]=key
    return newdic

class Entity:
    def __init__(self,env,name,print_actions=False,log=True):
     
        self.env=env
        
        self.name=name
        env.last_entity_id+=1
        self.id=self.env.last_entity_id
        env.entity_names[self.id]=self.name+'('+str(self.id)+')'
        self.last_act_id=0
        self.act_dic={}
        self.attr={}
        self.print_actions=print_actions
        self.log=log
        self.usingResources={}

        #***logs
        self.schedule_log=np.array([[0,0,0]])#act_id,act_start_time,act_finish_time
        self._status_codes={'wait for':1,'get':2,'start':3,'finish':4,'put':5,'add':6}
        self.status_log=np.array([[0,0,0]])#time,entity_status_code,actid/resid
        self.waiting_log=np.array([[0,0,0,0]]) #resource_id,start_waiting,end_waiting,amount waiting for

        if print_actions:
            print(name+'('+str(self.id)+') is created, sim_time:',env.now)

      
    def activity(self,name,duration):

           
        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') start',name,', sim_time:',self.env.now)
        
        if name not in self.act_dic:
            self.last_act_id+=1
            self.act_dic[name]=self.last_act_id
        if self.log:
            self.schedule_log=np.append(self.schedule_log,[[self.act_dic[name],self.env.now,self.env.now+duration]],axis=0)
            self.status_log=np.append(self.status_log,[[self.env.now,self._status_codes['start'],self.act_dic[name]]],axis=0)

        yield self.env.timeout(duration)

        if self.print_actions:
            print(self.name+'('+str(self.id)+ ') finished',name,', sim_time:',self.env.now)
        if self.log:
            self.status_log=np.append(self.status_log,[[self.env.now,self._status_codes['finish'],self.act_dic[name]]],axis=0)

    def do(self,name,dur):
        try:
            return self.env.process(self.activity(name,dur))
        except:
            print('pmpy: error in do')


    def get(self,res,amount,priority=1,preemp=False):
        try:
            if type(res)==Resource:
                return self.env.process(res.get(self,amount))
            elif type(res)==PriorityResource:
                return self.env.process(res.get(self,amount,priority))
            elif type(res)==PreemptiveResource:
                return self.env.process(res.get(self,amount,priority,preemp))
        except:
            print('pmpy: error in get')

    def add(self,res,amount):
        return self.env.process(res.add(self,amount))

    def put(self,res,amount):
        return self.env.process(res.put(self,amount))

    def schedule(self):
        df=pd.DataFrame(data=self.schedule_log,columns=['activity','start_time','finish_time'])
        df['activity']=df['activity'].map(switchDic(self.act_dic))
        return df

    def waitingLog(self):
        df=pd.DataFrame(data=self.waiting_log,columns=['resource','start_waiting','end_waiting','resource_amount'])
        df['resource']=(df['resource'].map(self.env.resource_names))
        
        return df

    def statusLog(self):
        df=pd.DataFrame(data=self.status_log,columns=['time','status','actid/resid'])
        df['status']=df['status'].map(switchDic(self._status_codes))
        
        return df
'''
*****************************************
*****Resource Class*******************
*****************************************
'''
class GeneralResource():
    def __init__(self,env,name,capacity,init,print_actions=False,log=True):
        self.name=name
        self.env=env 
        self.log=log
        self.print_actions=print_actions
        env.last_res_id+=1
        self.id=env.last_res_id
        env.resource_names[self.id]=self.name+'('+str(self.id)+')'
        self._in_use=0
        self.container=simpy.Container(env, capacity,init)
        self.queue_length=0
        

        #logs
        self.status_log=np.array([[0,0,0,0]])#time,in-use,idle,queue-lenthg
        self.queue_log=np.array([[0,0,0,0]])#entityid,startTime,endTime,amount


    def queueLog(self):
        df=pd.DataFrame(data=self.queue_log,columns=['entity','start_time','finish_time','resource_amount'])
        df['entity']=df['entity'].map(self.env.entity_names)
        return df

    def statusLog(self):
        df=pd.DataFrame(data=self.status_log,columns=['time','in_use','idle','queue_lenthg'])
        return df

    
    def _request(self,entity,amount):
        self.queue_length+=1
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' requested',str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.status_log=np.append(self.status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=np.append(entity.status_log,[[self.env.now,entity._status_codes['wait for'],self.id]],axis=0)

    def _get(self,entity,amount):
        self.queue_length-=1
        self._in_use+=amount
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' got '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.status_log=np.append(self.status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=np.append(entity.status_log,[[self.env.now,entity._status_codes['get'],self.id]],axis=0)
        entity.usingResources[self]=amount

    def _add(self,entity,amount):
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' add '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.status_log=np.append(self.status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=np.append(entity.status_log,[[entity._status_codes['add'],self.id,self.env.now]],axis=0)

    def _put(self,entity,amount):
        if self not in entity.usingResources:
            raise Warning(entity.name, "did not got ", self.name,"to put it back")
        if self in entity.usingResources and entity.usingResources[self]<amount:
            raise Warning(entity.name, "did not got this many of",self.name, "to put it back")
        entity.usingResources[self]=entity.usingResources[self]-amount
        self._in_use-=amount
        if self.print_actions or entity.print_actions:
            print(entity.name+'('+str(entity.id)+')'
                  +' put back '+str(amount),self.name+'(s), sim_time:',self.env.now)
        if self.log:
            self.status_log=np.append(self.status_log,[[self.env.now,self._in_use,self.container.level,self.queue_length]],axis=0)
        if entity.log:
            entity.status_log=np.append(entity.status_log,[[entity._status_codes['put'],self.id,self.env.now]],axis=0)
        
    def level(self):
        return self.container.level

    def idle(self):
        return self.level()

    def in_use(self):
        return self._in_use     

    def capacity(self):
        return self.container.capacity



class Resource(GeneralResource):
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        super().__init__(env,name,capacity,init,print_actions,log)
        self.requests=[]

    def get(self,entity,amount):
        super()._request(entity,amount)
   
        start_waiting=self.env.now
        yield self.container.get(amount)
        super()._get(entity,amount)
        if self.log:
            self.queue_log=np.append(self.queue_log,[[entity.id,start_waiting,self.env.now,amount]],axis=0)
        if entity.log:
            entity.waiting_log=np.append(entity.waiting_log,[[self.id,start_waiting,self.env.now,amount]],axis=0)
          
            
    def add(self,entity,amount):
        yield self.container.put(amount)
        super()._add(entity,amount)

    def put(self,entity,amount):
        yield self.container.put(amount)
        super()._put(entity,amount)
        
class PriorityRequest():
    def __init__(self,entity,amount,priority):
        self.time=entity.env.now
        self.entity=entity
        self.amount=amount
        self.priority=priority
        self.flag=simpy.Container(entity.env,init=0)#show if the resource is obtained
        
    def __gt__(self,other_request):
        if self.priority==other_request.priority:
            if self.time==other_request.time:
                return self.amount<other_request.amount
            else:
                return self.time<other_request.time
        return self.priority<other_request.priority
    
    def __eq__(self,other_request):
        return self.priority==other_request.priority and self.time==other_request.time and self.amount==other_request.amount


    def __ge__(self,other_request):
        return self>other_request or self==other_request

        
class PriorityResource(GeneralResource):
    def __init__(self,env,name, init=1,capacity=1000,print_actions=False,log=True):
        super().__init__(env,name,capacity,init,print_actions,log)
        
        self.resource=simpy.PriorityResource(env,1)
        self.requestlist=[]

    def get(self,entity,amount,priority=1):
       
        
        super()._request(entity,amount)
        pr=PriorityRequest(entity,amount,priority)
        bisect.insort_left(self.requestlist,pr)
        yield self.env.timeout(0)
        yield entity.env.process(self.checkAllRequests())
        yield pr.flag.get(1) #flag shows that the resource is granted
        
    def checkAllRequests(self):
        while len(self.requestlist)>0 and self.requestlist[-1].amount<=self.container.level:
        
           
            r=self.requestlist.pop()
            yield self.container.get(r.amount)
            r.flag.put(1)
            super()._get(r.entity,r.amount)
            if self.log:
                self.queue_log=np.append(self.queue_log,[[r.entity.id,r.time,self.env.now,r.amount]],axis=0)
            if r.entity.log:
                r.entity.waiting_log=np.append(r.entity.waiting_log,[[self.id,r.time,self.env.now,r.amount]],axis=0)
            
    def add(self,entity,amount):
        yield self.container.put(amount)
        super()._add(entity,amount)
        return entity.env.process(self.checkAllRequests())

    def put(self,entity,amount):
        yield self.container.put(amount)
        super()._put(entity,amount)
        return entity.env.process(self.checkAllRequests())

class PreemptiveResource(PriorityResource):
    pass
    
'''
*****************************************
*****Environment Class*******************
*****************************************
'''
class Environment(simpy.Environment):
    def __init__(self):
        super().__init__()
        self.last_entity_id=0
        self.entity_names={}
        self.last_res_id=0
        self.resource_names={}
       
        
    def run(self,until=None):
        super().run(until)

    def create_entities(self,name,total_number,print_actions=False,log=True):
        Entities=[]
        for i in range(total_number):
            Entities.append(Entity(self,name,print_actions,log))
        return Entities

    def create(self,name,time_between_arrivals,number_of_arrivals,number_arrived_each_time,process,resource_list,print_actions=False,log=True):
        for i in range(number_of_arrivals):
            a=self.create_entities(name,number_arrived_each_time,print_actions)
            for e in a:
                self.process(process(e,resource_list))
            yield self.timeout(time_between_arrivals)
 
    
'''
*****************************
********future works*********
*****************************
'''
#visualiziation
#graphs of logs
#preempt for breakdown
#Or between resource requests
#input checks
### check each entity should be given to only one process and one environment
#create tests

        


