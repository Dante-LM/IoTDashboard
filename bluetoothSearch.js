const BarnowlHci = require('barnowl-hci');

let barnowl = new BarnowlHci();

barnowl.addListener(BarnowlHci.TestListener, {});

barnowl.on("raddec", function(raddec) {
  console.log(raddec);
});

barnowl.on("infrastructureMessage", function(message) {
  console.log(message);
});
