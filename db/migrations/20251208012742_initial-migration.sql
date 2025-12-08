-- migrate:up
-- cascade delete on user
CREATE TABLE "user" (
    "id" SERIAL PRIMARY KEY,
    "username" VARCHAR NOT NULL UNIQUE,
    "api_token" VARCHAR NOT NULL UNIQUE
);

CREATE TABLE "usage" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL REFERENCES "user"("id") ON DELETE CASCADE,
    "characters_used" INTEGER NOT NULL,
    "created_at" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX "idx_user_api_token" ON "user" ("api_token");
CREATE INDEX "idx_usage_user_id" ON "usage" ("user_id");

-- migrate:down
DROP INDEX IF EXISTS "idx_user_api_token";
DROP INDEX IF EXISTS "idx_usage_user_id";

DROP TABLE IF EXISTS "usage";
DROP TABLE IF EXISTS "user";
