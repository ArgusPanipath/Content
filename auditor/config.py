"""
Argus Configuration Module
Centralized configuration for Redis keys and system constants.
"""

# ============================================================================
# Redis Keys
# ============================================================================

# Leader election and consensus
LEADER_KEY = "argus:leader"
NODE_HEALTH_PREFIX = "argus:node:"  # Will be suffixed with node_id
HEARTBEAT_COUNTER = "argus:heartbeat_count"

# Task queue
LEADER_QUEUE = "argus:leader_queue"

# ============================================================================
# System Constants
# ============================================================================

# Leader election
LEADER_TTL = 5  # seconds - How long the leader lease lasts
HEARTBEAT_INTERVAL = 2  # seconds - How often to send heartbeat
HEARTBEAT_MISS_THRESHOLD = 3  # Number of missed heartbeats before considering leader dead

# Node health
NODE_HEALTH_TTL = 10  # seconds - TTL for node health keys

# Leader behavior
RANDOMISED_FILTER_PERCENTAGE = 0.20  # 20% - Percentage of graph results to select
GRAPH_SEARCH_INTERVAL = 10  # seconds - How often leader queries graph

# Follower behavior
TASK_TIMEOUT = 5  # seconds - BLPOP timeout for followers

# ============================================================================
# Mock Data Configuration
# ============================================================================

# Mock package clusters for graph search
MOCK_PACKAGE_CLUSTERS = [
    "react@16.0.0", "react@17.0.0", "react@18.0.0",
    "lodash@4.17.15", "lodash@4.17.20", "lodash@4.17.21",
    "express@4.16.0", "express@4.17.0", "express@4.18.0",
    "axios@0.19.0", "axios@0.21.0", "axios@1.0.0",
    "webpack@4.41.0", "webpack@5.0.0", "webpack@5.75.0",
    "babel-core@6.26.0", "babel-core@7.0.0",
    "moment@2.24.0", "moment@2.29.0",
    "jquery@3.3.1", "jquery@3.6.0",
    "angular@1.7.0", "angular@12.0.0", "angular@15.0.0",
    "vue@2.6.10", "vue@3.0.0", "vue@3.2.0",
    "typescript@3.7.0", "typescript@4.0.0", "typescript@5.0.0",
    "eslint@6.8.0", "eslint@7.0.0", "eslint@8.0.0",
    "jest@24.9.0", "jest@27.0.0", "jest@29.0.0",
    "mocha@7.0.0", "mocha@9.0.0", "mocha@10.0.0",
    "chai@4.2.0", "chai@4.3.0",
    "sinon@8.0.0", "sinon@12.0.0", "sinon@15.0.0",
    "prettier@1.19.0", "prettier@2.0.0", "prettier@3.0.0",
    "nodemon@2.0.0", "nodemon@2.0.20",
    "dotenv@8.2.0", "dotenv@16.0.0",
    "cors@2.8.5", "cors@2.8.6",
    "mongoose@5.9.0", "mongoose@6.0.0", "mongoose@7.0.0",
    "redis@3.0.0", "redis@4.0.0",
    "socket.io@2.3.0", "socket.io@4.0.0",
    "next@10.0.0", "next@12.0.0", "next@13.0.0",
    "nuxt@2.15.0", "nuxt@3.0.0",
    "svelte@3.38.0", "svelte@4.0.0",
    "tailwindcss@2.0.0", "tailwindcss@3.0.0",
    "vite@2.0.0", "vite@4.0.0",
    "esbuild@0.12.0", "esbuild@0.17.0",
    "rollup@2.0.0", "rollup@3.0.0",
    "parcel@2.0.0", "parcel@2.8.0",
    "gatsby@3.0.0", "gatsby@5.0.0",
    "remix@1.0.0", "remix@1.15.0",
    "astro@1.0.0", "astro@2.0.0",
    "prisma@3.0.0", "prisma@4.0.0",
    "graphql@15.0.0", "graphql@16.0.0",
    "apollo-server@3.0.0", "apollo-server@4.0.0",
    "fastify@3.0.0", "fastify@4.0.0",
    "koa@2.13.0", "koa@2.14.0",
    "hapi@20.0.0", "hapi@21.0.0",
    "nest@8.0.0", "nest@9.0.0",
    "strapi@3.6.0", "strapi@4.0.0",
    "sanity@2.0.0", "sanity@3.0.0",
    "contentful@9.0.0", "contentful@10.0.0",
    "firebase@9.0.0", "firebase@10.0.0",
    "supabase@2.0.0", "supabase@2.20.0",
    "playwright@1.20.0", "playwright@1.30.0",
    "cypress@9.0.0", "cypress@12.0.0",
    "vitest@0.20.0", "vitest@0.30.0",
    "pnpm@7.0.0", "pnpm@8.0.0",
    "yarn@3.0.0", "yarn@4.0.0",
    "turbo@1.0.0", "turbo@1.10.0",
    "nx@14.0.0", "nx@16.0.0",
]

# Mock CVE database
MOCK_CVE_DATABASE = {
    "react": ["CVE-2021-23840", "CVE-2020-15168"],
    "lodash": ["CVE-2021-23337", "CVE-2020-8203", "CVE-2019-10744"],
    "express": ["CVE-2022-24999", "CVE-2021-23343"],
    "axios": ["CVE-2021-3749", "CVE-2020-28168"],
    "webpack": ["CVE-2021-23383", "CVE-2020-28469"],
    "moment": ["CVE-2022-31129", "CVE-2022-24785"],
    "jquery": ["CVE-2020-11023", "CVE-2020-11022"],
    "angular": ["CVE-2022-25844", "CVE-2021-23053"],
    "vue": ["CVE-2021-23337"],
    "socket.io": ["CVE-2022-2421"],
    "mongoose": ["CVE-2022-24304"],
    "graphql": ["CVE-2021-41248"],
}
