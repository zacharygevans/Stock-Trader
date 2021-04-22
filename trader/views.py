import base64
import datetime as dt
import urllib
from decimal import Decimal
from io import BytesIO

import matplotlib as mpl
import mplfinance as mpf
import pandas_datareader as pdr
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from pandas_datareader._utils import RemoteDataError

from .models import Stock, Transaction

mpl.use('agg')


def get_stock_data(stock):
    now = dt.datetime.now()
    start = now - dt.timedelta(days=60)
    df = pdr.get_data_yahoo(stock ,start , now)
    return df


def build_graph(data):
    imgdata = BytesIO()
    style = mpf.make_mpf_style(base_mpf_style='yahoo', rc={'font.size': 6})
    mpf.plot(data, type='candle', style=style, figscale=0.5, savefig=imgdata)
    imgdata.seek(0)
    string = base64.b64encode(imgdata.read())
    uri =  urllib.parse.quote(string)
    return uri


def validate_quantity(quantity):
    error = ''
    try:
        quantity = int(quantity)
        if quantity <= 0:
            error = 'quantity must be positive'
    except ValueError:
        error = 'quantity must be an integer'
    return quantity, error


@login_required
def index(request):
    user = request.user
    stocks = Stock.objects.filter(user=user)
    stock = request.GET.get('stock')
    error = request.GET.get('error', '')
    data, graph, current_price,= None, None, None
    if request.method == 'POST':
        stock = request.POST.get('stock')
        if not stock:
            error = 'You must select stock'
        else:
            stock = stock.upper()
            price = Decimal(request.POST.get('price'))
            quantity = request.POST.get('quantity')
            quantity, error = validate_quantity(quantity)
            if not error:
                total = price * quantity
                if total < user.balance:
                    user.balance -= total
                    user.save()
                    stock_model, created = Stock.objects.get_or_create(
                        user=user,
                        name=stock,
                        defaults={'quantity': quantity}
                    )
                    if not created:
                        stock_model.quantity += quantity
                        stock_model.save()
                    Transaction.objects.create(stock=stock_model, price=-total, quantity=quantity)
                else:
                    error = 'Not enough user balance to buy {quantity} {stock} at {price:.2f}'.format(
                        quantity=quantity,
                        stock=stock,
                        price=price,
                    )
    found = False
    if stock:
        try:
            df = get_stock_data(stock)
            found = True
            current_price = df.iloc[-1]['Close']
            graph = build_graph(df)
        except RemoteDataError:
            error = 'No data found'
        except Exception:
            error = 'Something went wrong'
    context = {
        'stocks': stocks,
        'found': found,
        'stock': stock,
        'data': data,
        'graph': graph,
        'current_price': current_price,
        'error': error,
    }
    return render(request, 'index.html', context)


def sell(request):
    error = ''
    if request.method == 'POST':
        user = request.user
        stocks = Stock.objects.filter(user=user)
        stock = request.POST.get('stock')
        if not stock:
            error = 'You must select stock'
        else:
            stock = stock.upper()
            stock_model = stocks.get(name=stock)
            quantity = request.POST.get('quantity')
            quantity, error = validate_quantity(quantity)
            if not error:
                df = get_stock_data(stock)
                current_price = Decimal(df.iloc[-1]['Close'])
                if quantity <= stock_model.quantity:
                    total = current_price * quantity
                    Transaction.objects.create(stock=stock_model, price=total, quantity=quantity)
                    stock_model.quantity -= quantity
                    stock_model.save()
                    user.balance += total
                    user.save()
                else:
                    error = 'Not enough {stock} to sell'.format(stock=stock)
    redirect_url = '/'
    if error:
        redirect_url += '?error={error}'.format(error=error)
    return HttpResponseRedirect(redirect_url)


def reset(request):
    request.user.balance = 1000
    request.user.save()
    Stock.objects.filter(user=request.user).delete()
    return HttpResponseRedirect('/')
