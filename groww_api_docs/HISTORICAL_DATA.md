# Historical Data

This guide describes how to fetch historical data of instruments easily using the SDK.

## [Get Historical Candle Data](#get-historical-candle-data)

> **Note**
>
> This method is deprecated and will be removed in future releases. Please use `get_historical_candles` method instead. See [here](/trade-api/docs/python-sdk/backtesting#get-historical-candle-data) for more details.

### [Python SDK Usage](#python-sdk-usage)

Fetch historical candle data for an instrument using this `get_historical_candle_data` method.

```
from growwapi import GrowwAPI
import time

# Groww API Credentials (Replace with your actual credentials)
API_AUTH_TOKEN = "your_token"

# Initialize Groww API
groww = GrowwAPI(API_AUTH_TOKEN)

# you can give time programatically.
end_time_in_millis = int(time.time() * 1000) # epoch time in milliseconds
start_time_in_millis = end_time_in_millis - (24 * 60 * 60 * 1000) # last 24 hours

# OR

# you can give start time and end time in yyyy-MM-dd HH:mm:ss format.
end_time = "2025-02-27 14:00:00"
start_time = "2025-02-27 10:00:00"

historical_data_response = groww.get_historical_candle_data(
    trading_symbol="RELIANCE",
    exchange=groww.EXCHANGE_NSE,
    segment=groww.SEGMENT_CASH,
    start_time=start_time,
    end_time=end_time,
    interval_in_minutes=5 # Optional: Interval in minutes for the candle data
)
print(historical_data_response)
```

#### [Request Schema](#request-schema)

| Name                | Type   | Description                                                                                      |
| ------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| exchange `*`        | string | [Stock exchange](/trade-api/docs/python-sdk/annexures#exchange)                                  |
| segment `*`         | string | [Segment](/trade-api/docs/python-sdk/annexures#segment) of the instrument such as CASH, FNO etc. |
| trading_symbol `*`  | string | Trading Symbol of the instrument as defined by the exchange                                      |
| start_time `*`      | string | Time in YYYY-MM-DD HH:mm:ss or epoch milliseconds format from which data is required             |
| end_time `*`        | string | Time in YYYY-MM-DD HH:mm:ss or epoch milliseconds format till when data is required              |
| interval_in_minutes | string | Interval in minutes for which data is required                                                   |

`*`required parameters

### [Response Payload](#response-payload)

All prices in rupees

```
{
  "candles": [
    [
      1633072800, // candle timestamp in epoch second
      150, // open price
      155, // high price
      145, // low price
      152, // close price
      10000 // volume
    ]
  ],
  "start_time": 2025-01-01 15:30:00,
  "end_time": 2025-01-01 15:30:00,
  "interval_in_minutes": 5
}
```

#### [Response Schema](#response-schema)

| Name                | Type           | Description                                                                                                                                                              |
| ------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| candles             | array\[array\] | This contains the list of candles. Each candle has candle timestamp (epoch second), open (float), high (float), low (float), close (float) , volume (int) in that order. |
| start_time          | string         | Start time in yyyy-MM-dd HH:mm:ss                                                                                                                                        |
| end_time            | string         | End time in yyyy-MM-dd HH:mm:ss                                                                                                                                          |
| interval_in_minutes | int            | Interval in minutes                                                                                                                                                      |

| Candle Interval        | Max Duration per Request | Historical Data Available |
| ---------------------- | ------------------------ | ------------------------- |
| **1 min**              | 7 days                   | Last 3 months             |
| **5 min**              | 15 days                  | Last 3 months             |
| **10 min**             | 30 days                  | Last 3 months             |
| **1 hour (60 min)**    | 150 days                 | Last 3 months             |
| **4 hours (240 min)**  | 365 days                 | Last 3 months             |
| **1 day (1440 min)**   | 1080 days (~3 years)     | Full history              |
| **1 week (10080 min)** | No Limit                 | Full history              |

[

Previous

Live Data

](/trade-api/docs/python-sdk/live-data)[

Next

Backtesting

](/trade-api/docs/python-sdk/backtesting)
