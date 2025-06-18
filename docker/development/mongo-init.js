// This script initializes both main and test databases
function initializeDatabase(dbName) {
    db = db.getSiblingDB(dbName);

// Create collections with validators
db.createCollection('movies', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'year', 'storage_id', 'format'],
      properties: {
        title: {
          bsonType: 'string',
          description: 'Movie title - required'
        },
        year: {
          bsonType: 'int',
          description: 'Release year - required'
        },
        storage_id: {
          bsonType: 'objectId',
          description: 'Reference to storage location - required'
        },
        format: {
          enum: ['DVD', 'Blu-ray', 'Digital'],
          description: 'Media format - required'
        },
        tmdb_id: {
          bsonType: 'int',
          description: 'TMDB movie ID'
        },
        genre: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'List of genres'
        },
        runtime: {
          bsonType: 'int',
          description: 'Movie runtime in minutes'
        },
        cover_image: {
          bsonType: 'string',
          description: 'URL to cover image'
        }
      }
    }
  }
});

db.createCollection('storage', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'type'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Storage location name - required'
        },
        description: {
          bsonType: 'string',
          description: 'Storage location description'
        },
        type: {
          enum: ['cabinet', 'shelf', 'bin', 'drawer'],
          description: 'Type of storage location - required'
        },
        parent_id: {
          bsonType: ['objectId', 'null'],
          description: 'Reference to parent storage location'
        },
        path: {
          bsonType: 'array',
          items: {
            bsonType: 'objectId'
          },
          description: 'Materialized path of ancestor IDs'
        },
        metadata: {
          bsonType: 'object',
          properties: {
            capacity: {
              bsonType: ['int', 'null'],
              description: 'Storage capacity'
            },
            dimensions: {
              bsonType: ['string', 'null'],
              description: 'Physical dimensions'
            },
            location: {
              bsonType: ['string', 'null'],
              description: 'Physical location or coordinates'
            },
            custom: {
              bsonType: 'object',
              description: 'Custom metadata fields'
            }
          }
        }
      }
    }
  }
});

db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'password_hash'],
      properties: {
        username: {
          bsonType: 'string',
          description: 'Username - required'
        },
        password_hash: {
          bsonType: 'string',
          description: 'Hashed password - required'
        },
        email: {
          bsonType: 'string',
          description: 'User email'
        }
      }
    }
  }
});

// Create indexes
db.movies.createIndex({ "title": 1 });
db.movies.createIndex({ "storage_id": 1 });
db.movies.createIndex({ "tmdb_id": 1 }, { unique: true, sparse: true });

// Storage indexes for tree operations
db.storage.createIndex({ "name": 1 }, { unique: true });
db.storage.createIndex({ "parent_id": 1 });
db.storage.createIndex({ "path": 1 });
db.storage.createIndex({ "type": 1 });
db.storage.createIndex({ "parent_id": 1, "type": 1 });
db.storage.createIndex({ "path": 1, "type": 1 });

db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });

}

// Initialize main database
initializeDatabase('media_manager');

// Initialize test database
initializeDatabase('media_manager_test');

// Create application user with credentials from environment variables
const appUsername = process.env.MONGO_APP_USERNAME || 'app_user';
const appPassword = process.env.MONGO_APP_PASSWORD || 'app_password';

// Create application user
db = db.getSiblingDB('media_manager');
db.createUser({
  user: appUsername,
  pwd: appPassword,
  roles: [
    {
      role: 'readWrite',
      db: 'media_manager'
    }
  ]
});

// Create test user with additional permissions for test databases
db = db.getSiblingDB('media_manager_test');
db.createUser({
  user: 'test_user',
  pwd: 'test_password',
  roles: [
    {
      role: 'readWrite',
      db: 'media_manager_test'
    },
    {
      role: 'dbAdmin',
      db: 'media_manager_test'
    }
  ]
});
