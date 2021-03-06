# -*- coding: utf-8 -*-
from ast import literal_eval
import xmltodict
import pandas as pd
import os
import sqlite3
from sqlite3 import Error


root_path = os.path.dirname(os.path.abspath( __file__ ))+"/../.."


class Database:
    @classmethod
    def create_connection(self,source):
        try:
            connection = sqlite3.connect(root_path+source)
            connection.row_factory=sqlite3.Row
            return connection
        except Error as e:
            print(e)
            
        return None
    
    
    def __init__(self,config):
        self.source = config['@source']
        self.type = config['@type']
        self.connection = self.create_connection(self.source)
        
    @staticmethod           
    def init(file):
        with open(file) as fd:
            doc = xmltodict.parse(fd.read())
            return Database(doc['dataloadEnv']['datasource'])
    
    def insert(self,entity):
        columns = []
        fields = []
        param_phold=[]
        #map input csv values to the database columns for insert
        for key,value in entity.fieldToColumn.items():
            columns.append(value)
            fields.append(key)
            param_phold.append('?')
            
        #append topic attributes to the table column and list the keys from config
        topics=[]
        if entity.topicFieldColumn != None:
            for key,value in entity.topicFieldToColumn.items():
                columns.append(value)
                topics.append(key)
                param_phold.append('?')
        
        param = (str(param_phold)[1:-1]).replace("'","")
        sql_insert='INSERT OR IGNORE INTO {} ({}) VALUES({})'.format(entity.name,str(columns)[1:-1],param)
        value_list =[]
        
            
        for idx,row in entity.df.iterrows():
            values=[]
            for field in fields:
                values.append(row[field])
            
            #map topics
            if entity.topicFieldColumn != None:
                topic_dict=literal_eval(row[entity.topicFieldColumn])
                for topic in topics:
                    if topic in topic_dict:
                        values.append(True)
                    else:
                        values.append(False)
            
        
            value_list.append(tuple(values));
        try:
            self.connection.cursor().executemany(sql_insert,value_list)
            self.connection.commit();
        except Error as e:
            print(e)
        
    def load(self,entity,reset):
        """ This method takes argument entity and reset table flag(reset True will delete all the current data in db)"""
        if reset == True:
            print("deleting {}".format(entity.name))
            delete_sql_string = "DELETE FROM {}".format(entity.name)
            self.connection.execute(delete_sql_string)
            self.connection.commit();
        self.insert(entity)
        
    def query(self,sql):
        self.connection.cursor.execute(sql)
        return self.connection.cursor.fetchall()
        