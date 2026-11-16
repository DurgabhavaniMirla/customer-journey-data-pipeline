# Data Dictionary & Database Schema

## Entity Relationship Diagram (Text Representation)
* `customer` (1) ---> (M) `session`
* `session` (1) ---> (M) `journey_event`
* `session` (1) ---> (M) `cart`
* `session` (1) ---> (0,1) `order`
* `session` (1) ---> (0,1) `support_ticket`
* `session` (1) ---> (1) `experiment`
* `session` (1) ---> (1) `journey_outcome`
* `product` (1) ---> (M) `cart`
* `page` (1) ---> (M) `journey_event` (implicit via URL)

## Entities (10 Core Entities)
1. **customer**: Master user profiles. (customer_id [PK], consent_status)
2. **session**: Traffic sessions. (session_id [PK], customer_id [FK])
3. **page**: Website hierarchy. (page_id [PK])
4. **product**: Catalog items. (product_id [PK])
5. **journey_event**: Clickstream interactions. (event_id [PK], session_id [FK])
6. **cart**: Intermediate transaction states (Bridge). (cart_id [PK], product_id [FK])
7. **order**: Successful conversions. (order_id [PK], session_id [FK])
8. **support_ticket**: Friction logs. (ticket_id [PK], session_id [FK])
9. **experiment**: A/B testing variants. (experiment_id [PK], session_id [FK])
10. **journey_outcome**: Final derived session state. (outcome_id [PK], session_id [FK])

## Business Rules & Funnel Definitions
* **Sessionization:** Grouped by `session_id`, bounded by `start_time` and the final chronological event.
* **Funnel Sequence:** page_view -> click -> add_to_cart -> checkout.
* **Anomaly Taxonomy:** bot_traffic_spike, ingestion_ordering_anomaly, duplicate_conversion, anonymous_id_merge_error.
