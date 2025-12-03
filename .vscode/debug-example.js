// Пример для отладки JavaScript в VS Code
// 1. Поставь breakpoint на строке 8 (кликни слева от номера)
// 2. Нажми F5 и выбери "Debug Node.js Script"
// 3. Используй F10 для пошагового выполнения

function calculateSum(numbers) {
  let sum = 0;
  for (const num of numbers) {
    sum += num; // Поставь breakpoint здесь
  }
  return sum;
}

function processData(data) {
  const numbers = data.map(item => item.value);
  const total = calculateSum(numbers);
  const average = total / numbers.length;

  return {
    total,
    average,
    count: numbers.length
  };
}

// Тестовые данные
const testData = [
  { id: 1, value: 10 },
  { id: 2, value: 20 },
  { id: 3, value: 30 }
];

console.log('Starting calculation...');
const result = processData(testData);
console.log('Result:', result);

// В Debug Console попробуй:
// - result
// - testData[0]
// - calculateSum([1, 2, 3])
