#!/usr/bin/env node

// Simple dice roller
// Usage: node roll.js [sides]
//   sides defaults to 6 (standard die)

const sides = parseInt(process.argv[2]) || 6;

if (isNaN(sides) || sides < 2) {
  console.error("Please provide a valid number of sides (minimum 2).");
  process.exit(1);
}

const result = Math.floor(Math.random() * sides) + 1;

console.log(`🎲 Rolling a d${sides}...`);
console.log(`   Result: ${result}`);
