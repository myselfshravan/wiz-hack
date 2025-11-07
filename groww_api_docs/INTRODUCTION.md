# Introduction

Welcome to the Groww Trading API! Our APIs enable you to build and automate trading strategies with seamless access to real-time market data, order placement, portfolio management, and more. Whether you're an experienced algo trader or just starting with automation, Groww's API is designed to be simple, powerful, and developer-friendly.

This SDK wraps our REST-like APIs into easy-to-use Python methods, allowing you to focus on building your trading applications without worrying about the underlying API implementation details.

With the Groww SDK, you can easily execute and modify orders in real time, manage your portfolio, access live market data, and more — all through a clean and intuitive Python interface.

## [Key Features](#key-features)

- Trade with Ease: Place, modify, and cancel orders across Equity & F&O.
- Real-time Market Data: Fetch live market prices, historical data, and order book depth.
- Secure Authentication: Use industry-standard OAuth 2.0 for seamless and secure access.
- Comprehensive SDK: Get started quickly with our Python SDK.
- WebSockets for Streaming: Subscribe to real-time market feeds and order updates.

---

## [Getting started:](#getting-started)

### [Step 1: Prerequisites](#step-1-prerequisites)

Trading on Groww using Groww APIs requires:

- A Groww account.
- Basic knowledge of Python and REST APIs.
- A development environment with Python 3.9+ installed.
- Having an active Trading API Subscription. You can purchase a subscription from this [page](https://groww.in/user/profile/trading-apis).

> **Important:** Groww Trading APIs currently support equity (CASH) and derivatives (FNO) trading only. Commodities trading (MCX segment) is not available at this time.

### [Step 2: Install the Python SDK](#step-2-install-the-python-sdk)

You can install the Python SDK by running this command on your terminal/command prompt.

\[data-radix-scroll-area-viewport\]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}\[data-radix-scroll-area-viewport\]::-webkit-scrollbar{display:none}

```
pip install growwapi
```

### [Step 3: Authentication](#step-3-authentication)

There are two ways you can interact with GrowwAPI:

### [1st Approach: API Key and Secret Flow](#1st-approach-api-key-and-secret-flow)

(Uses API Key and Secret — Requires daily approval on Groww Cloud Api Keys Page)

Make sure you have the latest SDK version for this. You can upgrade your Python SDK by running this command on your terminal/command prompt.

```
pip install --upgrade growwapi
```

- Go to the [Groww Cloud API Keys Page](https://groww.in/trade-api/api-keys).
- Log in to your Groww account.
- Click on ‘Generate API key’.
- Enter the name for the key and click Continue.
- Copy API Key and Secret. You can manage all your keys from the same page

You can use the generated ‘API key & secret’ to log in via the Python SDK in the following way:

```
from growwapi import GrowwAPI
import pyotp

api_key = "YOUR_API_KEY"
secret = "YOUR_API_SECRET"

access_token = GrowwAPI.get_access_token(api_key=api_key, secret=secret)
# Use access_token to initiate GrowwAPi
growwapi = GrowwAPI(access_token)
```

### [2nd Approach: TOTP Flow](#2nd-approach-totp-flow)

(Uses TOTP token and TOTP QR code — No Expiry)

Make sure you have the latest SDK version for this. You can upgrade your Python SDK by running this command on your terminal/command prompt.

```
pip install --upgrade growwapi
```

- Go to the [Groww Cloud API Keys Page](https://groww.in/trade-api/api-keys).
- Log in to your Groww account.
- Click on ‘Generate TOTP token’ which is under the dropdown to `Generate API Key` button.
- Enter the name for the key and click Continue.
- Copy the TOTP token and Secret or scan the QR via a third party authenticator app.
- You can manage all your keys from the same page.

To use the TOTP flow, you have to install the `pyotp` library. You can do that by running this command on your terminal/command prompt.

```
pip install pyotp
```

You can use the generated ‘API key & secret’ to log in via the Python SDK in the following way:

```
from growwapi import GrowwAPI
import pyotp

api_key = "YOUR_TOTP_TOKEN"

# totp can be obtained using the authenticator app or can be generated like this
totp_gen = pyotp.TOTP('YOUR_TOTP_SECRET')
totp = totp_gen.now()

access_token = GrowwAPI.get_access_token(api_key=api_key, totp=totp)
# Use access_token to initiate GrowwAPi
growwapi = GrowwAPI(access_token)
```

### [Step 4: Place your First Order](#step-4-place-your-first-order)

Use this sample code to place an order.

```
from growwapi import GrowwAPI

# Groww API Credentials (Replace with your actual credentials)
API_AUTH_TOKEN = "your_token"  # Access token generated using step 3.,

# Initialize Groww API
groww = GrowwAPI(API_AUTH_TOKEN)

place_order_response = groww.place_order(
    trading_symbol="WIPRO",
    quantity=1,
    validity=groww.VALIDITY_DAY,
    exchange=groww.EXCHANGE_NSE,
    segment=groww.SEGMENT_CASH,
    product=groww.PRODUCT_CNC,
    order_type=groww.ORDER_TYPE_LIMIT,
    transaction_type=groww.TRANSACTION_TYPE_BUY,
    price=250,               # Optional: Price of the stock (for Limit orders)
    trigger_price=245,       # Optional: Trigger price (if applicable)
    order_reference_id="Ab-654321234-1628190"  # Optional: User provided 8 to 20 length alphanumeric reference ID to track the order
)
print(place_order_response)
```

## [Rate Limits](#rate-limits)

The rate limits are applied at the type level, not on individual APIs. This means that all APIs grouped under a type (e.g., Orders, Live Data, Non Trading) share the same limit. If the limit for one API within a type is exhausted, all other APIs in that type will also be rate-limited until the limit window resets.

| Type        | Requests                                                          | Limit (Per second) | Limit (Per minute) |
| ----------- | ----------------------------------------------------------------- | ------------------ | ------------------ |
| Orders      | Create, Modify and Cancel Order                                   | 15                 | 250                |
| Live Data   | Market Quote, LTP, OHLC                                           | 10                 | 300                |
| Non Trading | Order Status, Order list, Trade list, Positions, Holdings, Margin | 20                 | 500                |
