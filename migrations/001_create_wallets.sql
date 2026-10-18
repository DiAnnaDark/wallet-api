
CREATE TABLE wallets (
    id UUID PRIMARY KEY,
    balance NUMERIC(18, 2) NOT NULL DEFAULT 0,
    CONSTRAINT balance_nonnegative CHECK (balance >= 0),
    CONSTRAINT balance_maximum CHECK (balance <= 9999999999999999.99)
);
