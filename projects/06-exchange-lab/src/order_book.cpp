#include "order_book.hpp"
#include <algorithm>
#include <cctype>
#include <limits>
#include <stdexcept>

namespace exchange_lab {
namespace {
bool valid_id(const std::string& id) {
    if (id.empty() || id.size() > 128) return false;
    for (unsigned char c : id) {
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-')) return false;
    }
    return true;
}

bool better(const Order& candidate, const Order& current, Side incoming) {
    if (candidate.price != current.price)
        return incoming == Side::buy ? candidate.price < current.price : candidate.price > current.price;
    return candidate.sequence < current.sequence;
}
}

std::vector<Event> OrderBook::submit(const std::string& id, Side side, std::int64_t price, std::int64_t quantity) {
    if (!valid_id(id) || (side != Side::buy && side != Side::sell) || price <= 0 || quantity <= 0)
        throw std::invalid_argument("Invalid order");
    if (seen_ids_.find(id) != seen_ids_.end()) throw std::invalid_argument("Order ID already used");
    if (next_sequence_ == std::numeric_limits<std::uint64_t>::max()) throw std::overflow_error("Order sequence exhausted");
    const auto sequence = next_sequence_++;
    seen_ids_.insert(id);
    std::vector<Event> events;
    while (quantity > 0) {
        auto best = orders_.end();
        for (auto it = orders_.begin(); it != orders_.end(); ++it) {
            const Order& resting = it->second;
            const bool crosses = side == Side::buy ? price >= resting.price : price <= resting.price;
            if (resting.side == side || !crosses) continue;
            if (best == orders_.end() || better(resting, best->second, side)) best = it;
        }
        if (best == orders_.end()) break;
        const std::int64_t amount = std::min(quantity, best->second.remaining);
        events.push_back({"fill", id, best->second.id, best->second.price, amount});
        quantity -= amount;
        best->second.remaining -= amount;
        if (best->second.remaining == 0) orders_.erase(best);
    }
    if (quantity > 0) {
        orders_.emplace(id, Order{id, side, price, quantity, sequence});
        events.push_back({"rest", id, "", price, quantity});
    }
    return events;
}

Event OrderBook::cancel(const std::string& id) {
    auto it = orders_.find(id);
    if (it == orders_.end()) throw std::invalid_argument("Open order not found");
    Event event{"cancel", id, "", it->second.price, it->second.remaining};
    orders_.erase(it);
    return event;
}

std::vector<Order> OrderBook::open_orders() const {
    std::vector<Order> result;
    for (const auto& item : orders_) result.push_back(item.second);
    std::sort(result.begin(), result.end(), [](const Order& a, const Order& b) { return a.sequence < b.sequence; });
    return result;
}
}
