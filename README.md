# expense-tracker


sudo -u postgres psql
    \c expenses
    \dt



### Webhook
Stripe CLI
如果测试的是支付相关的 webhook，可以使用 Stripe CLI 来触发事件：

```
stripe listen --forward-to localhost:5000/webhook
stripe trigger payment_intent.succeeded
```
