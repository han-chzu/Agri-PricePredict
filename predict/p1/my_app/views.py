﻿from django.shortcuts import render
from django.http import HttpResponse
from django import http
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
import pandas as pd
import numpy as np
import datetime
import pymysql
from sqlalchemy import create_engine
from datetime import date, datetime

#调整json日期类型数据
class ComplexEncoder(json.JSONEncoder):  
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

mysql_setting = {
        'host': '47.100.201.211',
        'port': 3306,
        'user': 'root',
        'passwd': 'iyGfLR64Ne4Ddhk7',
        # 数据库名称
        'db': 'data',
        'charset': 'utf8'
    }
engine = create_engine("mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(**mysql_setting),max_overflow=5)
sql_cmd = "select product from CountyProduct"
pls = pd.read_sql(sql_cmd, engine)
pl = pls['product'].values


def predict(product, span):
    main = product
    # 通过sqlalchemy库连接mysql
    mysql_setting = {
            'host': '47.100.201.211',
            'port': 3306,
            'user': 'root',
            'passwd': 'iyGfLR64Ne4Ddhk7',
            # 数据库名称
            'db': 'data',
            'charset': 'utf8'
        }
    engine = create_engine("mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(**mysql_setting),max_overflow=5)
    # advice和relation表共用先获取
    sql_cmd = "select * from predictAdvice1"
    advice1 = pd.read_sql(sql_cmd, engine)
    sql_cmd = "select * from predictAdvice2"
    advice2 = pd.read_sql(sql_cmd, engine)
    sql_cmd = "select * from productRelation where product = %(product)s"
    relation = pd.read_sql(sql_cmd, engine, params={'product': product})
    # 首选农产品价格预测
    def mainPredict(product, span):
        # 判断是长期预测还是短期预测
        if span == 0:
            sql_cmd = "select * from predict_online_short where product = %(product)s"
            data_online = pd.read_sql(sql_cmd, engine, params={'product': product})
            sql_cmd = "select * from predict_offline_short where product = %(product)s"
            data_offline = pd.read_sql(sql_cmd, engine, params={'product': product})
        elif span == 1:
            sql_cmd = "select * from predict_online_long where product = %(product)s"
            data_online = pd.read_sql(sql_cmd, engine, params={'product': product})
            sql_cmd = "select * from predict_offline_long where product = %(product)s"
            data_offline = pd.read_sql(sql_cmd, engine, params={'product': product})
        price_predict = [] # 存放所有线上线下价格
    # 判断是否有线上价格和线下价格
        # 有线下价格
        if data_offline.empty and data_online.empty:
            return False
        if not data_offline.empty: 
            mainproduct = {}
            mainproduct["name"] = product
            mainproduct["online"] = 0
            # pricelist[{"date": , "predict price":}]
            df_offline = []
            df1 = data_offline.rename(columns={"price":"predict_price"})
            df2 = df1[["date", "predict_price"]].to_dict('index')
            for i in df2.values():
                df_offline.append(i)
            mainproduct["pricelist"] = df_offline
            price_predict.append(mainproduct)
            # 有线上价格
        if not data_online.empty: 
            mainproduct = {}
            mainproduct["name"] = product
            mainproduct["online"] = 1
            mainproduct["span"] = 0
            mainproduct["consumer_advice"] = advice1.loc[advice1['product']==product]['consumer advice'].values[0]
            # pricelist价格
            df_online = [] 
            df3 = data_online.rename(columns={"price":"predict_price"})
            df4 = df3[["date", "predict_price"]].to_dict('index')
            for i in df4.values():
                df_online.append(i)
            mainproduct["pricelist"] = df_online
            price_predict.append(mainproduct)
        return price_predict


    def predictOther(product, span):
        # 判断是长期预测还是短期预测
        if span == 0:
            sql_cmd = "select * from predict_online_short where product = %(product)s"
            data_online = pd.read_sql(sql_cmd, engine, params={'product': product})
            sql_cmd = "select * from predict_offline_short where product = %(product)s"
            data_offline = pd.read_sql(sql_cmd, engine, params={'product': product})
        elif span == 1:
            sql_cmd = "select * from predict_online_long where product = %(product)s"
            data_online = pd.read_sql(sql_cmd, engine, params={'product': product})
            sql_cmd = "select * from predict_offline_long where product = %(product)s"
            data_offline = pd.read_sql(sql_cmd, engine, params={'product': product})
        price_predict_other  = [] # 存放所有线上线下价格
        # 有线下价格
        if not data_offline.empty: 
            mainproduct = {}
            mainproduct["name"] = product
            mainproduct["online"] = 0
            mainproduct["span"] = 0
            df_offline = []
            df1 = data_offline.rename(columns={"price":"predict_price"})
            df2 = df1[["date", "predict_price"]].to_dict('index')
            for i in df2.values():
                df_offline.append(i)
            mainproduct["pricelist"] = df_offline
            price_predict_other.append(mainproduct)
            # 有线上价格
        if not data_online.empty: 
            mainproduct = {}
            mainproduct["name"] = product
            mainproduct["online"] = 1
            mainproduct["span"] = 0
            mainproduct["seller_advice"] = advice2.loc[(advice2['main']==main)&(advice2['cp']==product), 'seller advice'].values[0]
            # pricelist价格
            df_online = [] 
            df3 = data_online.rename(columns={"price":"predict_price"})
            df4 = df3[["date", "predict_price"]].to_dict('index')
            for i in df4.values():
                df_online.append(i)
            mainproduct["pricelist"] = df_online
            mainproduct
            price_predict_other.append(mainproduct)
        return price_predict_other    
    
    # 竞品（cp）价格预测
    def cpPredict(product, span):
        cp_price_predict = []
        # 获取竞品关系(先判断有无竞品)
        if relation["cpProduct"][0] is not None:
            cplist = [x for x in relation["cpProduct"][0].split()]
            for cpProduct in cplist:
                for i in predictOther(cpProduct, span):
                    cp_price_predict.append(i)
        return cp_price_predict
    # 替代品（sub）价格预测
    def subPredict(product, span):
        sub_price_predict = []
        # 获取替代品关系(先判断有无替代品)
        if relation["subProduct"][0] is not None:
            sublist = [x for x in relation["subProduct"][0].split()]
            for subProduct in sublist:
                for i in predictOther(subProduct, span):
                    sub_price_predict.append(i)
        return sub_price_predict
    def getPrice(product, span):
        data = {}
        data["price_predict"] = []
        data["cp_price_predict"] = []
        data["sub_price_predict"] = []
        for i in mainPredict(product, span):
            data["price_predict"].append(i)
        for i in cpPredict(product, span):
            data["cp_price_predict"].append(i)
        for i in subPredict(product, span):
            data["sub_price_predict"].append(i)
        return data
    return getPrice(product, span)

def comparePrice(product, start, end):
    # 通过sqlalchemy库连接mysql
    mysql_setting = {
            'host': '47.100.201.211',
            'port': 3306,
            'user': 'root',
            'passwd': 'iyGfLR64Ne4Ddhk7',
            # 数据库名称
            'db': 'data',
            'charset': 'utf8'
        }
    engine = create_engine("mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(**mysql_setting),max_overflow=5)
    sql_cmd = "select * from productRelation where product = %(product)s"
    relation = pd.read_sql(sql_cmd, engine, params={'product': product})
    def mainCompare(product):
        df_all = []
        main_product_compare = {}
        main_product_compare['name'] = product
        main_product_compare['span'] = 0
        sql_cmd = "select * from price_real_predict_compare_short where product = %(product)s and date >= %(start)s and date <= %(end)s"
        dt = pd.read_sql(sql_cmd, engine, params={'product': product, 'start':start, 'end':end})
        dt = dt.fillna('')
        df_online = [] 
        dt1 = dt[["date", "real_price", "predict_price"]].to_dict('index')
        for i in dt1.values():
            df_online.append(i)
        main_product_compare["pricelist"] = df_online
        df_all.append(main_product_compare)
        return df_all
    def cpCompare(product):
        cp_product_compare = []
        # 获取竞品关系(先判断有无竞品)
        if relation["cpProduct"][0] is not None:
            cplist = [x for x in relation["cpProduct"][0].split()]
            for cpProduct in cplist:
                for i in mainCompare(cpProduct):
                    cp_product_compare.append(i)
        return cp_product_compare
    def getAll(product):
        data = {}
        data["main_product_compare"] = []
        data["cp_product_compare"] = []
        for i in mainCompare(product):
            data["main_product_compare"].append(i)
        for i in cpCompare(product):
            data["cp_product_compare"].append(i)
        return data
    return getAll(product)


@csrf_exempt
def CountyProduct(request):
    # 通过sqlalchemy库连接mysql
    mysql_setting = {
        'host': '47.100.201.211',
        'port': 3306,
        'user': 'root',
        'passwd': 'iyGfLR64Ne4Ddhk7',
        # 数据库名称
        'db': 'data',
        'charset': 'utf8'
    }
    engine = create_engine("mysql+pymysql://{user}:{passwd}@{host}:{port}/{db}".format(**mysql_setting),max_overflow=5) 
    product = {}
    product["data"] = []
    sql_cmd = "SELECT * FROM data.CountyProduct"
    CountyProduct = pd.read_sql(sql_cmd, engine)
    for i in CountyProduct.groupby(by='county'):
        obj = {}
        obj['county'] = i[0]
        product["data"].append(obj)
    for i in product["data"]:
        i['productlist'] = []
        for j in CountyProduct.iterrows():
            if (j[1]['county'] == i['county']):
                i['productlist'].append(j[1]['product'])
    countyproduct = json.dumps(product, ensure_ascii=False)
    return JsonResponse({"code":4, "message": "成功查询", "data": json.loads(countyproduct)}
                    ,json_dumps_params={'ensure_ascii':False})



@csrf_exempt
def PricePredict(request):
    if request.method == 'GET':  # 当提交表单时
        # 判断是否传参
        if request.GET:
            product = request.GET.get('product')
            if product in pl:
                span = request.GET.get('span')
                try: 
                    predictprice = predict(product, int(span))
                    price = json.dumps(predictprice, cls=ComplexEncoder, ensure_ascii=False)
                    return JsonResponse({"code":4, "message": "成功查询", "data": json.loads(price)}
                    ,json_dumps_params={'ensure_ascii':False})
                except:
                    return JsonResponse({"code":3, "message": "数据库中暂无该农产品", "data": None},
                                json_dumps_params={'ensure_ascii':False})
            else:
                return JsonResponse({"code":2, "message": "输入商品不属于示范县农产品", "data": None},
                                json_dumps_params={'ensure_ascii':False})
        else:
            return JsonResponse({"code":1, "message": "输入为空", "data": None},
                                json_dumps_params={'ensure_ascii':False})

    else:
        return JsonResponse({"code":0, "message": "方法错误", "data": None},
                                json_dumps_params={'ensure_ascii':False})


@csrf_exempt
def PriceCompare(request):
    if request.method == 'GET':  # 当提交表单时
        # 判断是否传参
        if request.GET:
            product = request.GET.get('product')
            if product in pl:
                startDate = request.GET.get('startDate')
                endDate = request.GET.get('endDate')
                try: 
                    predictprice = comparePrice(product, startDate, endDate)
                    price = json.dumps(predictprice, cls=ComplexEncoder, ensure_ascii=False)
                    return JsonResponse({"code":4, "message": "成功查询", "data": json.loads(price)}
                    ,json_dumps_params={'ensure_ascii':False})
                except:
                    return JsonResponse({"code":3, "message": "传入时间参数有误", "data": None},
                                json_dumps_params={'ensure_ascii':False})
            else:
                return JsonResponse({"code":2, "message": "输入商品不属于示范县农产品", "data": None},
                                json_dumps_params={'ensure_ascii':False})
        else:
            return JsonResponse({"code":1, "message": "输入为空", "data": None},
                                json_dumps_params={'ensure_ascii':False})

    else:
        return JsonResponse({"code":0, "message": "方法错误", "data": None},
                                json_dumps_params={'ensure_ascii':False})
