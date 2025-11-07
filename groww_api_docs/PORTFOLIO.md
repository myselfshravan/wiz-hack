# Portfolio

This guide describes how to get detailed information about your holdings and positions using our Python SDK.

## [Get Holdings](#get-holdings)

Use the `get_holdings_for_user` method to fetch your current holdings quickly and see all your stocks in one place.

Holdings represent the user's collection of long-term equity delivery stocks. An asset in a holdings portfolio stays there indefinitely unless it is sold, delisted, or modified by the exchanges. Fundamentally, the assets in the holdings are stored in the user's DEMAT account, as processed by exchanges and clearing institutions.

### [Python SDK Usage](#python-sdk-usage)

```
from growwapi import GrowwAPI

# Groww API Credentials (Replace with your actual credentials)
API_AUTH_TOKEN = "your_token"

# Initialize Groww API
groww = GrowwAPI(API_AUTH_TOKEN)

# Optional: timeout parameter (in seconds) for the API call; default is typically set by the SDK.
holdings_response = groww.get_holdings_for_user(timeout=5)
print(holdings_response)
```

### [Response Payload](#response-payload)

All prices in rupees

```
"holdings": [
  {
    "isin": "INE545U01014",
    "trading_symbol": "RELIANCE",
    "quantity": 10,
    "average_price": 100,
    "pledge_quantity": 2,
    "demat_locked_quantity": 1,
    "groww_locked_quantity": 1.5,
    "repledge_quantity": 0.5,
    "t1_quantity": 3,
    "demat_free_quantity": 5,
    "corporate_action_additional_quantity": 1,
    "active_demat_transfer_quantity": 1
  }
]
```

#### [Response Schema](#response-schema)

| Name                                 | Type   | Description                                                             |
| ------------------------------------ | ------ | ----------------------------------------------------------------------- |
| isin                                 | string | The ISIN (International Securities Identification number) of the symbol |
| trading_symbol                       | string | The trading symbol of the holding                                       |
| quantity                             | float  | The net quantity of the holding                                         |
| average_price                        | int    | The average price of the holding                                        |
| pledge_quantity                      | float  | The pledged quantity of the holding                                     |
| demat_locked_quantity                | float  | The demat locked quantity of the holding                                |
| groww_locked_quantity                | float  | The Groww locked quantity of the holding                                |
| repledge_quantity                    | float  | The repledged quantity of the holding                                   |
| t1_quantity                          | float  | The T1 quantity of the holding                                          |
| demat_free_quantity                  | float  | The demat free quantity of the holding                                  |
| corporate_action_additional_quantity | int    | The corporate action additional quantity of the holding                 |
| active_demat_transfer_quantity       | int    | The active demat transfer quantity of the holding                       |

## [Get Positions for User](#get-positions-for-user)

Fetch all positions associated with your account using this `get_positions_for_user` method.

### [Python SDK Usage](#python-sdk-usage-1)

```
from growwapi import GrowwAPI

# Groww API Credentials (Replace with your actual credentials)
API_AUTH_TOKEN = "your_token"

# Initialize Groww API
groww = GrowwAPI(API_AUTH_TOKEN)

user_positions_response = groww.get_positions_for_user() # returns positions of both CASH and FNO segment.
cash_positions_response = groww.get_positions_for_user(segment=groww.SEGMENT_CASH) # returns positions of CASH segment.

print(user_positions_response)
```

#### [Request Schema](#request-schema)

| Name    | Type   | Description                                                                                      |
| ------- | ------ | ------------------------------------------------------------------------------------------------ |
| segment | string | [Segment](/trade-api/docs/python-sdk/annexures#segment) of the instrument such as CASH, FNO etc. |

`*`required parameters

### [Response Payload](#response-payload-1)

All prices in rupees

```

"positions": [
  {
    "trading_symbol": "RELIANCE",
    "segment": "CASH",
    "credit_quantity": 10,
    "credit_price": 12500,
    "debit_quantity": 5,
    "debit_price": 12000,
    "carry_forward_credit_quantity": 8,
    "carry_forward_credit_price": 12300,
    "carry_forward_debit_quantity": 3,
    "carry_forward_debit_price": 11800,
    "exchange": "NSE",
    "symbol_isin": "INE123A01016",
    "quantity": 15,
    "product": "CNC",
    "net_carry_forward_quantity": 10,
    "net_price": 12400,
    "net_carry_forward_price": 12200,
    "realised_pnl": 500,
  }
]
```

#### [Response Schema](#response-schema-1)

| Name                          | Type   | Description                                                                                      |
| ----------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| trading_symbol                | string | Trading symbol of the instrument                                                                 |
| segment                       | string | [Segment](/trade-api/docs/python-sdk/annexures#segment) of the instrument such as CASH, FNO etc. |
| credit_quantity               | int    | Quantity of credited instruments                                                                 |
| credit_price                  | int    | Average price in rupees of credited instruments                                                  |
| debit_quantity                | int    | Quantity of debited instruments                                                                  |
| debit_price                   | int    | Average price in rupees of debited instruments                                                   |
| carry_forward_credit_quantity | int    | Quantity of carry forward credited instruments                                                   |
| carry_forward_credit_price    | int    | Average price in rupees of carry forward credited instruments                                    |
| carry_forward_debit_quantity  | int    | Quantity of carry forward debited instruments                                                    |
| carry_forward_debit_price     | int    | Average price in rupees of carry forward debited instruments                                     |
| exchange                      | string | [Stock exchange](/trade-api/docs/python-sdk/annexures#exchange)                                  |
| symbol_isin                   | string | ISIN (International Securities Identification number) of the symbol                              |
| quantity                      | int    | Net quantity of instruments                                                                      |
| product                       | string | [Product type](/trade-api/docs/python-sdk/annexures#product)                                     |
| net_carry_forward_quantity    | int    | Net carry forward quantity of instruments                                                        |
| net_price                     | int    | Net average price in rupees of instruments                                                       |
| net_carry_forward_price       | int    | Net average price in rupees of carry forward instruments                                         |
| realised_pnl                  | int    | Realised profit and loss in rupees                                                               |

## [Get Position for Symbol](#get-position-for-symbol)

Retrieve detailed position information for a specific symbol using this `get_position_for_trading_symbol`.

### [Python SDK Usage](#python-sdk-usage-2)

```
from growwapi import GrowwAPI

# Groww API Credentials (Replace with your actual credentials)
API_AUTH_TOKEN = "your_token"

# Initialize Groww API
groww = GrowwAPI(API_AUTH_TOKEN)

trading_symbol_position_response = groww.get_position_for_trading_symbol(trading_symbol="RELIANCE", segment=groww.SEGMENT_CASH)
print(trading_symbol_position_response)
```

#### [Request Schema](#request-schema-1)

| Name               | Type   | Description                                                                                      |
| ------------------ | ------ | ------------------------------------------------------------------------------------------------ |
| trading_symbol `*` | string | Trading symbol of the instrument.                                                                |
| segment `*`        | string | [Segment](/trade-api/docs/python-sdk/annexures#segment) of the instrument such as CASH, FNO etc. |

`*`required parameter

### [Response Payload](#response-payload-2)

All prices in rupees

```
{
  "positions": [
    {
      "trading_symbol": "RELIANCE",
      "segment": "CASH",
      "credit_quantity": 10,
      "credit_price": 12500,
      "debit_quantity": 5,
      "debit_price": 12000,
      "carry_forward_credit_quantity": 8,
      "carry_forward_credit_price": 12300,
      "carry_forward_debit_quantity": 3,
      "carry_forward_debit_price": 11800,
      "exchange": "NSE",
      "symbol_isin": "INE123A01016",
      "quantity": 15,
      "product": "CNC",
      "net_carry_forward_quantity": 10,
      "net_price": 12400,
      "net_carry_forward_price": 12200,
      "realised_pnl": 500
    }
  ]
}
```

#### [Response Schema](#response-schema-2)

| Name                          | Type   | Description                                                                                      |
| ----------------------------- | ------ | ------------------------------------------------------------------------------------------------ |
| trading_symbol                | string | Trading symbol of the instrument.                                                                |
| segment                       | string | [Segment](/trade-api/docs/python-sdk/annexures#segment) of the instrument such as CASH, FNO etc. |
| credit_quantity               | int    | Quantity of credited instruments                                                                 |
| credit_price                  | int    | Average price in rupees of credited instruments                                                  |
| debit_quantity                | int    | Quantity of debited instruments                                                                  |
| debit_price                   | int    | Average price in rupees of debited instruments                                                   |
| carry_forward_credit_quantity | int    | Quantity of carry forward credited instruments                                                   |
| carry_forward_credit_price    | int    | Average price in rupees of carry forward credited instruments                                    |
| carry_forward_debit_quantity  | int    | Quantity of carry forward debited instruments                                                    |
| carry_forward_debit_price     | int    | Average price in rupees of carry forward debited instruments                                     |
| exchange                      | string | [Stock exchange](/trade-api/docs/python-sdk/annexures#exchange)                                  |
| symbol_isin                   | string | ISIN (International Securities Identification number) of the symbol                              |
| quantity                      | int    | Net quantity of instruments                                                                      |
| product                       | string | [Product type](/trade-api/docs/python-sdk/annexures#product)                                     |
| net_carry_forward_quantity    | int    | Net carry forward quantity of instruments                                                        |
| net_price                     | int    | Net average price in rupees of instruments                                                       |
| net_carry_forward_price       | int    | Net average price in rupees of carry forward instruments                                         |
| realised_pnl                  | int    | Realised profit and loss in rupees                                                               |

[

Previous

Smart Orders

](/trade-api/docs/python-sdk/smart-orders)[

Next

Margin

](/trade-api/docs/python-sdk/margin)
