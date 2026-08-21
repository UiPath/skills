#!/usr/bin/env node

// Dice Roller - rolls a standard 6-sided die

const sides = 6;
const result = Math.floor(Math.random() * sides) + 1;

console.log(`Rolling a ${sides}-sided die...`);
console.log(`You rolled: ${result}`);
