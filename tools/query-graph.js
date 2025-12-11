#!/usr/bin/env bun
// Скрипт для прямого доступа к SQLite базе ultrascript-tools

const { Database } = require('bun:sqlite');

const dbPath = 'C:\\Users\\Администратор\\AppData\\Local\\UltraScriptTools\\projects\\9ef9lt\\graph.db';
const db = Database.open(dbPath);

// Получить список таблиц
function getTables() {
  const tables = db.query('SELECT name FROM sqlite_master WHERE type="table"').all();
  return tables;
}

// Получить схему таблицы
function getTableSchema(tableName) {
  const schema = db.query(`PRAGMA table_info(${tableName})`).all();
  return schema;
}

// Получить статистику
function getStats() {
  const entities = db.query('SELECT COUNT(*) as count FROM entities').get();
  const relationships = db.query('SELECT COUNT(*) as count FROM relationships').get();
  const files = db.query('SELECT COUNT(*) as count FROM files').get();

  return {
    entities: entities.count,
    relationships: relationships.count,
    files: files.count
  };
}

// Получить все сущности
function getEntities(limit = 10) {
  const entities = db.query('SELECT * FROM entities LIMIT ?').all(limit);
  return entities;
}

// Поиск по имени
function searchByName(name) {
  const entities = db.query('SELECT * FROM entities WHERE name LIKE ?').all(`%${name}%`);
  return entities;
}

// Получить сущности по типу
function getEntitiesByType(type, limit = 20) {
  const entities = db.query('SELECT * FROM entities WHERE type = ? LIMIT ?').all(type, limit);
  return entities;
}

// Получить все типы сущностей
function getEntityTypes() {
  const types = db.query('SELECT DISTINCT type, COUNT(*) as count FROM entities GROUP BY type ORDER BY count DESC').all();
  return types;
}

// Получить файлы
function getFiles(limit = 20) {
  const files = db.query('SELECT * FROM files LIMIT ?').all(limit);
  return files;
}

// Main
const command = process.argv[2] || 'stats';

switch (command) {
  case 'tables':
    console.log(JSON.stringify(getTables(), null, 2));
    break;
  case 'schema':
    const tableName = process.argv[3] || 'entities';
    console.log(JSON.stringify(getTableSchema(tableName), null, 2));
    break;
  case 'stats':
    console.log(JSON.stringify(getStats(), null, 2));
    break;
  case 'entities':
    const limit = parseInt(process.argv[3]) || 10;
    console.log(JSON.stringify(getEntities(limit), null, 2));
    break;
  case 'search':
    const searchName = process.argv[3];
    if (!searchName) {
      console.error('Usage: bun query-graph.js search <name>');
      process.exit(1);
    }
    console.log(JSON.stringify(searchByName(searchName), null, 2));
    break;
  case 'types':
    console.log(JSON.stringify(getEntityTypes(), null, 2));
    break;
  case 'by-type':
    const entityType = process.argv[3];
    const typeLimit = parseInt(process.argv[4]) || 20;
    if (!entityType) {
      console.error('Usage: bun query-graph.js by-type <type> [limit]');
      process.exit(1);
    }
    console.log(JSON.stringify(getEntitiesByType(entityType, typeLimit), null, 2));
    break;
  case 'files':
    const filesLimit = parseInt(process.argv[3]) || 20;
    console.log(JSON.stringify(getFiles(filesLimit), null, 2));
    break;
  default:
    console.log('Usage: bun query-graph.js [tables|schema|stats|entities|search|types|by-type|files]');
}

db.close();
