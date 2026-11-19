"""Small labelled synthetic fixtures for data quality and session coverage."""
import unittest
import pandas as pd
from backend.data.validation.validator import inspect_raw_dataframe


class TestDataQuality(unittest.TestCase):
    def inspect(self, frame):
        return inspect_raw_dataframe(frame, 'synthetic_fixture', start_date='2015-01-01',end_date='2015-01-06')

    def fixture(self):
        return pd.DataFrame({'date':['2015-01-02','2015-01-05','2015-01-06'], 'Adj Close':[25.,25.1,25.2]})

    def test_complete_sessions_pass(self):
        report, output = self.inspect(self.fixture())
        self.assertTrue(report['passed'])
        self.assertEqual(report['calendar']['expected_session_count'],3)
        self.assertEqual(len(output),3)

    def test_missing_middle_or_endpoint_rejected(self):
        for index in range(3):
            with self.subTest(index=index):
                report, output = self.inspect(self.fixture().drop(index))
                self.assertFalse(report['passed'])
                self.assertEqual(len(report['calendar']['missing_sessions']),1)
                self.assertTrue(output.empty)

    def test_weekend_and_holiday_rejected(self):
        for date in ['2015-01-03','2015-01-01']:
            with self.subTest(date=date):
                frame = pd.concat([self.fixture(),pd.DataFrame({'date':[date],'Adj Close':[25.]})],ignore_index=True).sort_values('date')
                report,_ = self.inspect(frame)
                self.assertFalse(report['passed'])
                self.assertIn(date,report['calendar']['unexpected_sessions'])

    def test_bad_dates_prices_duplicates_and_order_rejected(self):
        for value in [None,float('nan'),float('inf'),float('-inf'),0,-1,'bad']:
            with self.subTest(price=value):
                frame=self.fixture(); frame['Adj Close']=frame['Adj Close'].astype(object); frame.loc[1,'Adj Close']=value
                report,output=self.inspect(frame)
                self.assertFalse(report['passed']); self.assertTrue(output.empty)
        for dates in [['2015-01-02','bad','2015-01-06'],['2015-01-02','2015-01-02','2015-01-06'],['2015-01-06','2015-01-05','2015-01-02'],['2015-01-02','2015-1-5','2015-01-06']]:
            with self.subTest(dates=dates):
                frame=self.fixture(); frame['date']=dates
                self.assertFalse(self.inspect(frame)[0]['passed'])

    def test_empty_and_missing_columns_rejected(self):
        for frame in [self.fixture().iloc[:0],self.fixture().drop(columns='date'),self.fixture().drop(columns='Adj Close')]:
            self.assertFalse(self.inspect(frame)[0]['passed'])

    def test_large_market_moves_flagged_without_removal(self):
        frame=self.fixture(); frame.loc[1,'Adj Close']=30.
        report,output=self.inspect(frame)
        self.assertTrue(report['passed'])
        self.assertTrue(report['warnings'])
        self.assertEqual(len(output),3)
        self.assertEqual(report['rows_removed'],0)

    def test_auxiliary_ohlc_and_volume_checked(self):
        frame=self.fixture().assign(Open=25.,High=26.,Low=24.,Close=25.,Volume=100)
        self.assertTrue(self.inspect(frame)[0]['passed'])
        for column,value in [('Volume',-1),('High',20.),('Low',30.),('Close',float('inf'))]:
            with self.subTest(column=column):
                bad=frame.copy(); bad[column]=bad[column].astype(float); bad.loc[0,column]=value
                self.assertFalse(self.inspect(bad)[0]['passed'])

if __name__ == '__main__': unittest.main()
