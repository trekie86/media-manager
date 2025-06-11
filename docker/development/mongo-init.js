// This script initializes the MongoDB database with default collections
db = db.getSiblingDB('media_manager');

// Create collections with validators
db.createCollection('movies', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['title', 'year', 'bin_id', 'format'],
      properties: {
        title: {
          bsonType: 'string',
          description: 'Movie title - required'
        },
        year: {
          bsonType: 'int',
          description: 'Release year - required'
        },
        bin_id: {
          bsonType: 'objectId',
          description: 'Reference to storage bin - required'
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

db.createCollection('bins', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'Bin name - required'
        },
        description: {
          bsonType: 'string',
          description: 'Bin description'
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
db.movies.createIndex({ "bin_id": 1 });
db.movies.createIndex({ "tmdb_id": 1 }, { unique: true, sparse: true });
db.bins.createIndex({ "name": 1 }, { unique: true });
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true, sparse: true });

// Create application user with credentials from environment variables
const appUsername = process.env.MONGO_APP_USERNAME || 'app_user';
const appPassword = process.env.MONGO_APP_PASSWORD || 'app_password';

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
