# bapp/sales_predictor.py

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from bapp.models import Purchase
import os

def generate_sales_prediction():
    purchases = Purchase.objects.all().order_by('date_purchased')

    if not purchases.exists():
        # Avoid running prediction if no data is available
        return None

    # Convert QuerySet to DataFrame with only date_purchased
    data = pd.DataFrame(list(purchases.values('date_purchased')))
    
    if 'date_purchased' not in data.columns or data.empty:
        return None

    # Ensure datetime format
    data['date_purchased'] = pd.to_datetime(data['date_purchased'])
    data['count'] = 1

    # Group by date and prepare training data
    daily_sales = data.groupby('date_purchased').count().reset_index()
    daily_sales['day_number'] = (daily_sales['date_purchased'] - daily_sales['date_purchased'].min()).dt.days

    X = daily_sales[['day_number']]
    y = daily_sales['count']

    model = LinearRegression()
    model.fit(X, y)

    future_days = pd.DataFrame({'day_number': range(X['day_number'].max() + 1, X['day_number'].max() + 8)})
    predictions = model.predict(future_days)

    # Plot actual and predicted
    plt.figure(figsize=(10, 5))
    plt.plot(daily_sales['date_purchased'], y, label='Actual Sales')
    future_dates = [daily_sales['date_purchased'].max() + pd.Timedelta(days=i) for i in range(1, 8)]
    plt.plot(future_dates, predictions, label='Predicted Sales', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Units Sold')
    plt.title('Sales Forecast')
    plt.legend()
    plt.grid()

    image_path = 'static/sales_forecast.png'
    plt.savefig(image_path)
    plt.close()
    return image_path
