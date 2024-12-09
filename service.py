import time
import requests
from requests import RequestException
from stock import Stock

NINJA_API_KEY = "t7kGKURsW31xlUX9jhmX6Q==JKxHUYND1othy0fC"
API_URL = 'https://api.api-ninjas.com/v1/stockprice?ticker={}'


class StockService:
    def __init__(self):
        # dict since we need to support CRUD operations for specific stocks by id
        self.portfolio = {}
        self.nextid = 1

    def add_stock(self, symbol: str, purchase_price: float, shares: int,
                  name: str = 'NA', purchase_date: str = 'NA') -> Stock:
        """
        If the ‘name’ or ‘purchase date’ is not supplied for a stock on the POST
        request, the JSON representation for those fields is the string ‘NA’ (Not
        Available). E.g., that is what the server returns for those fields in a GET request.
        The validity is checked in the controller layer.
        """
        stock_id = str(self.nextid)
        self.nextid += 1
        new_stock = Stock(stock_id, name, symbol, round(purchase_price, 2), purchase_date, shares)
        self.portfolio[stock_id] = new_stock
        return new_stock

    def get_stock_by_id(self, stock_id: str) -> Stock:
        if stock_id in self.portfolio:
            return self.portfolio[stock_id]
        else:
            raise KeyError(f"Stock with id '{stock_id}' not found in the portfolio.")

    def remove_stock(self, stock_id: str) -> None:
        if stock_id in self.portfolio:
            del self.portfolio[stock_id]
        else:
            raise KeyError(f"Stock with id '{stock_id}' not found in the portfolio.")

    def update_stock(self, stock_id: str, updated_data: dict) -> None:
        """
        Updates the stock with the given stock_id using the provided updated_data.
        """
        if stock_id not in self.portfolio:
            raise KeyError(f"Stock with ID '{stock_id}' not found.")

        stock = self.portfolio[stock_id]

        # Update stock fields with new values or retain existing ones
        stock.symbol = updated_data.get('symbol', stock.symbol)
        stock.name = updated_data.get('name', stock.name)
        stock.purchase_price = updated_data.get('purchase_price', stock.purchase_price)
        stock.purchase_date = updated_data.get('purchase_date', stock.purchase_date)
        stock.shares = updated_data.get('shares', stock.shares)

    def get_stock_value(self, stock_id: str) -> dict:
        try:
            stock = self.get_stock_by_id(stock_id)
        except KeyError:
            raise KeyError(f"Stock with ID '{stock_id}' not found.")
        try:
            current_price = round(self.fetch_stock_current_price(stock.symbol), 2)
            stock_value = round(stock.shares * current_price, 2)

            # Return the required data as a dictionary
            return {
                "symbol": stock.symbol,
                "ticker": current_price,
                "stock value": stock_value
            }
        except Exception as e:
            raise ValueError(f"Error fetching stock value for '{stock.symbol}': {str(e)}")

    @staticmethod
    def fetch_stock_current_price(symbol: str, retries=3, delay=2) -> float:
        """
        For more info: https://api-ninjas.com/api/stockprice
        """
        for attempt in range(retries):
            try:
                # Ensure the symbol is valid and properly formatted
                symbol = symbol.strip().upper()
                response = requests.get(API_URL.format(symbol), headers={'X-Api-Key': NINJA_API_KEY}, timeout=10)

                if response.status_code == requests.codes.ok:
                    response_json = response.json()
                    if 'price' in response_json:
                        return response_json['price']
                    else:
                        # Treat empty or unexpected responses as invalid symbols
                        raise ValueError(f"Invalid stock symbol: {symbol}")
                else:
                    raise ValueError(f"Unexpected status code: {response.status_code}")

            except RequestException as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise ValueError(f"API request failed after {retries} attempts: {str(e)}")

    def get_stocks(self) -> list[dict[str, any]]:
        """
        Returns:
            A list of stock objects represented as dictionaries.
        """
        if not self.portfolio or not isinstance(self.portfolio, dict):
            return []

        return [stock.to_dict() for stock in self.portfolio.values()]

    def get_portfolio_value(self) -> float:
        total_value = 0.0
        try:
            for stock in self.portfolio.values():
                current_price = self.fetch_stock_current_price(stock.symbol)
                if current_price:
                    total_value += stock.shares * current_price
                else:
                    raise ValueError(f"Price for stock '{stock.symbol}' (id: {stock.id}) "
                                     f"is not available. Please update the symbol.")
            return round(total_value, 2)
        except Exception as e:
            raise ValueError(f"Error calculating portfolio value: {str(e)}")

    def symbol_exists(self, symbol: str) -> bool:
        return any(stock.symbol == symbol for stock in self.portfolio.values())

    def stock_id_exists(self, stock_id: str) -> bool:
        return stock_id in self.portfolio