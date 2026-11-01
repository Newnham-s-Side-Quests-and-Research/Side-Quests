#ifndef EXCHANGE_LAB_ORDER_BOOK_HPP
#define EXCHANGE_LAB_ORDER_BOOK_HPP

#include <cstdint>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace exchange_lab {
// Prices are integer ticks and quantities are integer lots. IDs cannot be reused.
// Matching uses price then arrival order and executes at the resting price.
enum class Side { buy, sell };

struct Order {
    std::string id;
    Side side;
    std::int64_t price;
    std::int64_t remaining;
    std::uint64_t sequence;
};

struct Event {
    std::string type;
    std::string incoming_id;
    std::string resting_id;
    std::int64_t price;
    std::int64_t quantity;
};

class OrderBook {
public:
    std::vector<Event> submit(const std::string& id, Side side, std::int64_t price, std::int64_t quantity);
    Event cancel(const std::string& id);
    std::vector<Order> open_orders() const;

private:
    std::uint64_t next_sequence_ = 0;
    std::unordered_map<std::string, Order> orders_;
    std::unordered_set<std::string> seen_ids_;
};
}
#endif
