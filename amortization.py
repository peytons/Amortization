import datetime
from decimal import Decimal
import decimal

ROUNDING_PAYMENTS = Decimal('0.01')  # Can be 0.01, 0.10, 1.00, 10.00, etc.
ROUNDING_METHOD   = decimal.ROUND_HALF_UP

def _typeless_round(n):
    if not ROUNDING_PAYMENTS:
        return n
    try:
        return n.quantize(ROUNDING_PAYMENTS, rounding=ROUNDING_METHOD)
    except AttributeError: # backward compatibility for floats
        import math
        return round(n, int(-math.log10(ROUNDING_PAYMENTS)))

def pmt(rate, nper, pv, typ=0):
    
    if rate < 0 or nper < 0 or pv < 0:
        Except("rate, nper and pv must be > 0")
    
    payment = (pv * rate) / (1 - (1 + rate)**(-nper))
    if typ: 
        payment /= (1 + rate)
    return _typeless_round(payment)

def presentValueOfAnnuity(cflw, rate, nper):
    return cflw * ((1 - (1 + rate)**(-nper)) / rate)


def schedule(rate, nper, pv, typ=0):
    payment = pmt(rate, nper, pv, typ)

    periods = []
    totalInterest = 0
    for period in range(nper):
        interest = _typeless_round(rate * pv)
        if period == nper-1:  # last payment
            payment = pv + interest
            principal = pv
        else:
            principal = payment - interest
        pv -= principal

        newPeriod = Period(interest, principal, pv, payment)
        periods.append(newPeriod)
    return periods

## these two functions feel like they belong somewhere.. like a subclass of datetime or something
def nextMonth(date):
    try:
        year = date.year
        month = date.month
        
        if month == 12:
            month = 0
            year += 1
            
        return datetime.date(year, month + 1, 1)
    except AttributeError:
        print('Must be a datetime.date object')
    except Exception as e:
        print(e)

def formatDate(date):
    if BILLING_PERIOD == MONTHLY_BILLING:
        return date.strftime("%B, %Y")
    return date.isoformat()

        

class Period:

    @property
    def interest(self): return self._interest
    @interest.setter
    def interest(self, interest):
        if type(interest) == int or type(interest) == float:
            self._interest = interest
        else:
            print("interest must be an int or float")

    @property
    def principal(self): return self._principal
    @principal.setter
    def principal(self, principal):
        if type(principal) == int or type(principal) == float:
            self._principal = principal
        else:
            print("principal must be an int or float")

    @property
    def balance(self): return self._balance
    @balance.setter
    def balance(self, balance):
        if type(balance) == int or type(balance) == float:
            self._balance = balance
        else:
            print("balance must be an int or float")

    @property
    def date(self): return self._date
    @date.setter
    def date(self, date):
        if type(date) == datetime.date or type(date) == type(None):
            self._date = date
        else: print("date must be a datetime.date object")
    

    def __init__(self, interest, principal, balance, payment, date=None):
        self.interest = interest
        self.principal = principal
        self.balance = balance
        self.date = date
        self.payment = payment

    def __str__(self):
        if self.date:
            return str('%15s   Payment: %7.2f   Interest: %7.2f   Principal: %7.2f   Balance: %7.2f' %
                  (formatDate(self.date), self.payment, self.interest, self.principal, self.balance))
        return str('Payment: %7.2f   Interest: %7.2f   Principal: %7.2f   Balance: %7.2f' %
                  (self.payment, self.interest, self.principal, self.balance))




class Loan:
    
    ## if the properties haven't been set they should be set automatically to 0
    ## check all conditions.. can things be negative ?
    @property
    def rate(self): return self._rate
    @rate.setter
    def rate(self, rate):
        if type(rate) == float and rate > 0: ## can rate be an int?
            self._rate = rate
        else: print("rate must be a float > 0")

    @property
    def nper(self): return self._nper
    @nper.setter
    def nper(self, nper):
        if type(nper) == int and nper > 0:
            self._nper = nper
        else: print("nper must be an int > 0")

    @property
    def pv(self): return self._pv
    @pv.setter
    def pv(self, pv):
        if (type(pv) == int or type(pv) == float) and pv > 0:
            self._pv = pv
        else: print("pv must be a float or int > 0")

    @property
    def date(self): return self._date
    @date.setter
    def date(self, date):
        if type(date) == datetime.date or type(date) == type(None):
            self._date = date
        else: print("date must be a datetime.date object")

    @property
    def typ(self): return self._typ
    @typ.setter
    def typ(self, typ):
        if typ == 0 or typ == 1:
            self._typ = typ
        else: print("typ must be 0 or 1")

        
    def __init__(self, rate, nper, pv, date=None, typ=0):
        self.rate = rate
        self.nper = nper
        self.pv = pv
        self.date = date
        self.typ = typ
        self.periods = []
        
    def __str__(self):
        if self.date:
            return str('%15s   Rate: %g   Nper: %g   Pv: %g   Typ: %g' %
                       (formatDate(self.date), self.rate, self.nper, self.pv, self.typ))
        return str('Rate: %g   Nper: %g   Pv: %g   Typ: %g' %
                   (self.rate, self.nper, self.pv, self.typ))


    def pmt(self):
        return pmt(self.rate, self.nper, self.pv, self.typ)

## this can be one function

    def period(self, period): 
        try:
            return self.periods[period-1]
        except IndexError:
            self.periods = schedule(self.rate, self.nper, self.pv, self.typ)
        if self.date:
            for n in range(self.nper):
                old = self.periods[n]
                newdate = self.dateForPeriod(n)
                self.periods[n] = Period(old.interest, old.principal, old.balance, old.payment, newdate)

        return self.periods[period-1]

    def schedule(self, startPeriod=1, endPeriod=None):
        periods = []

        if not endPeriod:
            endPeriod = self.nper

        period = startPeriod
        while period <= endPeriod:
            periods.append(self.period(period))
            period += 1

        return periods

##

    def periodForDate(self, date):
        if not self.date:
            print('No starting date entered')
            return
        if date < self.date:
            return('Date is before loan begins')

        period = 1
        currentDate = self.date

        while not((currentDate.year == date.year) and (currentDate.month == date.month)):
            currentDate = nextMonth(currentDate)
            period += 1
            
        return period


    def dateForPeriod(self, period):
        if not self.date:
            print('No starting date entered')
            return
        
        date = self.date
        i = 1
        while i < period:
            date = nextMonth(date)
            i += 1
        return date
    

    def printSchedule(self, startPeriod=1, endPeriod=None):
        period = startPeriod
        if not endPeriod:
            endPeriod = self.nper

        for n in range(startPeriod, endPeriod+1):
            print "Period %3d   %s" % (n, self.period(n))

        return

        # dead code -- left until dates are handled in schedule
        if self.date:
            while period <= endPeriod:
                currentPeriod = self.period(period)
                print(currentPeriod)
                period += 1
        else:
            while period <= endPeriod:
                currentPeriod = self.period(period)
                print('Period %3d   Interest: %7.2f   Principal: %7.2f   Balance: %7.2f' %
                      (period, currentPeriod.interest, currentPeriod.principal, currentPeriod.balance))
                period += 1
                

## can make these work with period OR dates simply by if datetime.date then find periodForDate bada bing bada boom
    def interestRemainingAfterPeriod(self, period):
        return self.totalInterest() - self.interestPaidSincePeriod(period)
    
    def interestPaidSincePeriod(self, period):
         payment = pmt(self.rate, self.nper, self.pv, self.typ)
         totalPaidThusFar = payment * period
         
         return totalPaidThusFar - self.principalPaidSincePeriod(period)

    def principalRemainingAfterPeriod(self, period):
        payment = pmt(self.rate, self.nper, self.pv, self.typ)
        remainingPeriods = self.nper - period
        
        return presentValueOfAnnuity(payment, self.rate, remainingPeriods)

    
    def principalPaidSincePeriod(self, period):
        return self.pv - self.principalRemainingAfterPeriod(period)
        
    def totalCost(self):
        return pmt(self.rate, self.nper, self.pv, self.typ) * self.nper

    def totalInterest(self):
        return self.totalCost() - self.pv

    def totalPaidSincePeriod(self, period):
        payment = pmt(self.rate, self.nper, self.pv, self.typ)
        return payment * period

    def totalRemainingAfterPeriod(self, period):
        return self.totalCost() - self.totalPaidSincePeriod(period)

    def payOffDate(self):
        return formatDate(self.period(self.nper).date)
    
