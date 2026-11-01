#include "../src/order_book.hpp"
#include <cassert>
#include <cstdint>
#include <limits>
#include <stdexcept>

using exchange_lab::OrderBook;
using exchange_lab::Side;

int main() {
    OrderBook book;
    book.submit("sell_a", Side::sell, 101, 5);
    book.submit("sell_b", Side::sell, 100, 3);
    book.submit("sell_c", Side::sell, 100, 4);
    const auto events = book.submit("buy_a", Side::buy, 101, 9);
    assert(events.size() == 3);
    assert(events[0].resting_id == "sell_b" && events[0].price == 100 && events[0].quantity == 3);
    assert(events[1].resting_id == "sell_c" && events[1].price == 100 && events[1].quantity == 4);
    assert(events[2].resting_id == "sell_a" && events[2].price == 101 && events[2].quantity == 2);
    const auto remaining = book.open_orders();
    assert(remaining.size() == 1 && remaining[0].id == "sell_a" && remaining[0].remaining == 3);
    assert(book.cancel("sell_a").quantity == 3);
    assert(book.open_orders().empty());
    bool rejected = false;
    try { book.submit("sell_a", Side::sell, 1, 1); } catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected && book.open_orders().empty());
    rejected = false;
    try { book.submit("bad", Side::buy, 0, 1); } catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected && book.open_orders().empty());
    rejected = false;
    try { book.cancel("absent"); } catch (const std::invalid_argument&) { rejected = true; }
    assert(rejected && book.open_orders().empty());
    book.submit("large", Side::buy, std::numeric_limits<std::int64_t>::max(), std::numeric_limits<std::int64_t>::max());
    auto fill = book.submit("seller", Side::sell, 1, 1);
    assert(fill.size() == 1 && fill[0].price == std::numeric_limits<std::int64_t>::max());
    assert(book.open_orders()[0].remaining == std::numeric_limits<std::int64_t>::max() - 1);
    return 0;
}
