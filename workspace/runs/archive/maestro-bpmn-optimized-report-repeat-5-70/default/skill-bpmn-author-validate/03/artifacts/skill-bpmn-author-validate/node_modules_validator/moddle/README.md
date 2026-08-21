# moddle

[![CI](https://github.com/bpmn-io/moddle/workflows/CI/badge.svg)](https://github.com/bpmn-io/moddle/actions?query=workflow%3ACI)

A utility library for working with meta-model based data structures.


## What is it good for?

[moddle](https://github.com/bpmn-io/moddle) offers you a concise way to define [meta models](https://en.wikipedia.org/wiki/Metamodeling) in JavaScript. You can use these models to consume documents, create model elements, and perform model validation.


### Define a schema

You start by creating a [moddle schema](./docs/descriptor.md). It is a [JSON](http://json.org/) file which describes types, their properties, and relationships:

```json
{
  "$schema": "https://unpkg.com/moddle/resources/schema/moddle.json",
  "name": "Cars",
  "uri": "http://cars",
  "prefix": "c",
  "types": [
    {
      "name": "Base",
      "properties": [
        { "name": "id", "type": "String", "isAttr": true }
      ]
    },
    {
      "name": "Root",
      "superClass": [ "Base" ],
      "properties": [
        { "name": "cars", "type": "Car", "isMany": true }
      ]
    },
    {
      "name": "Car",
      "superClass": [ "Base" ],
      "properties": [
        { "name": "name", "type": "String", "isAttr": true, "default": "No Name" },
        { "name": "power", "type": "Integer", "isAttr": true },
        { "name": "similar", "type": "Car", "isMany": true, "isReference": true },
        { "name": "trunk", "type": "Element", "isMany": true }
      ]
    }
  ]
}
```

You may attach the provided [JSON schema](./resources/schema/moddle.json) to get your moddle descriptor validated by code editor.


### Instantiate moddle

You can instantiate a moddle instance with a set of defined schemas:

```javascript
import { Moddle } from 'moddle';

var cars = new Moddle([ carsJSON ]);
```


### Create objects

Use a [moddle](https://github.com/bpmn-io/moddle) instance to create objects of your defined types:

```javascript
var taiga = cars.create('c:Car', { name: 'Taiga' });

console.log(taiga);
// { $type: 'c:Car', name: 'Taiga' };


var cheapCar = cars.create('c:Car');

console.log(cheapCar.name);
// "No Name"


// really?
cheapCar.get('similar').push(taiga);
```


### Introspect things

Then again, given the knowledge [moddle](https://github.com/bpmn-io/moddle) has, you can perform deep introspection:

```javascript
var carDescriptor = cheapCar.$descriptor;

console.log(carDescriptor.properties);
// [ { name: 'id', type: 'String', ... }, { name: 'name', type: 'String', ...} ... ]
```


### Access extensions

moddle is friendly towards extensions and keeps unknown _any_ properties around:

```javascript
taiga.set('specialProperty', 'not known to moddle');

console.log(taiga.get('specialProperty'));
// 'not known to moddle'
```

It also allows you to create _any_ elements for namespaces that you did not explicitly define:

```javascript
var screwdriver = cars.createAny('tools:Screwdriver', 'http://tools', {
  make: 'ScrewIt!'
});

car.trunk.push(screwdriver);
```


### There is more

Have a look at our [test coverage](https://github.com/bpmn-io/moddle/blob/master/test/spec) to learn about everything that is currently supported.


## Resources

* [Issues](https://github.com/bpmn-io/moddle/issues)
* [Examples](https://github.com/bpmn-io/moddle/tree/master/test/fixtures/model)
* [Documentation](https://github.com/bpmn-io/moddle/tree/master/docs)


## Related

* [moddle-xml](https://github.com/bpmn-io/moddle-xml): read xml documents based on moddle descriptors


## License

MIT
