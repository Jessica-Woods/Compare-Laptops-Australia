function cleanData(data) {
  data.forEach(laptop => {
    // We assume that SSDs are worth 5 times as much as regular
    // hard drives. This value is used to order the "storage" section.
    laptop.storage_value = laptop.storage.reduce((sum, storage) => {
      if(storage.is_ssd) {
        return sum + (5 * parseInt(storage.hdd_gbs));
      } else {
        return sum + parseInt(storage.hdd_gbs);
      }
    }, 0);

    // If we have multiple storages we want to combine them into
    // some useful text about what they are
    laptop.storage_text = laptop.storage.map(storage => {
      if(storage.is_ssd) {
        return storage.hdd_gbs + "GB SSD";
      } else {
        return storage.hdd_gbs + "GB HDD";
      }
    }).join(', ');
  });

  return data;
}

function createChart(data) {
  var canvasWidth = 1200;
  var canvasHeight = 600;

  var margin = {
    top: 40,
    right: 85,
    left: 85,
    bottom: 50
  };

  var w = canvasWidth - margin.left - margin.right;
  var h = canvasHeight - margin.top - margin.bottom;

  var svg = d3.select('#chart')
      .append('svg')
      .attr('class', 'graph')
      .attr('width', canvasWidth)
      .attr('height', canvasHeight);

    var innerCanvas = svg
      .append('g')
      .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');


    // Add a "data last updated" label
    svg
      .append('text')
      .attr('x', canvasWidth - 5)
      .attr('y', canvasHeight - 5)
      .style('fill', d3.color('#3A3535'))
      .attr('text-anchor', 'end')
      .text('Data last updated: 26/05/2019');

  return [innerCanvas, w, h];
}

function renderLaptopChart(svg, w, h, dimensions, data, table) {
  var xScale =
    d3.scalePoint()
      .domain(Object.keys(dimensions))
      .range([0, w]);

  // Add a yScale to each dimension
  Object.keys(dimensions).forEach(dim => {
    // Take a copy of the dimension data so our sorting doesn't break it
    var dimensionData = data.slice(0);

    // Sort the data before adding the scale if a sort function is defined
    if(dimensions[dim].sortFunction) {
      dimensionData.sort(dimensions[dim].sortFunction);
    }

    dimensionData = dimensionData.map(dimensions[dim].yValueFunction);

    var scale;
    if(dimensions[dim].scaleType === 'linear') {
      scale =
        d3.scaleLinear()
          .domain(d3.extent(dimensionData))
          .range([h, 0])
          .nice();
    } else if (dimensions[dim].scaleType === 'point') {
      scale =
        d3.scalePoint()
          .domain(dimensionData)
          .range([h, 0]);
    } else {
      throw dimensions[dim].scaleType + ' is not a valid domain type!';
    }

    dimensions[dim].yScale = scale;
  });

  var colour =
      d3.scaleSequential()
      .domain(d3.extent(data, d => +d['price_aud']))
      .interpolator(d3.interpolateRgb(d3.rgb('#6DBBAA'),d3.rgb('#FDA302')));

  // Draw our paths
  svg
    .selectAll('path.laptop')
    .data(data, d => d.url)
    .enter()
    .append('path')
    .attr('class', 'laptop')
    .attr('d', function(d) {
      var points = Object.keys(dimensions).map(dim => {
        return [
          xScale(dim),
          dimensions[dim].yScale(dimensions[dim].yValueFunction(d))
        ];
      });

      var lineFunction = d3.line();

      return lineFunction(points);
    })
    .style('fill', 'none')
    .style('stroke', d => colour(d.price_aud))
    .style('stroke-width', '2px')
    .append('svg:title')
    .text(d => d.name);

  // Add a group for each dimension
  var dimensionGroups = svg
    .selectAll('yAxis')
    .data(Object.keys(dimensions))
    .enter()
    .append('g')
      .attr('transform', d => 'translate(' + xScale(d) + ',0)');

  // Add axis and title for each dimension
  dimensionGroups
    .each(function(dim) {
      var axis =
        d3.axisLeft()
          .scale(dimensions[dim].yScale);

      if(dimensions[dim].tickFormat) {
        axis.tickFormat(dimensions[dim].tickFormat);
      }

      return d3.select(this).call(axis).attr('class', 'yAxis');
    })
    .append('text')
    .style('text-anchor', 'middle')
    .attr('class', 'y-axis-title')
    .attr('y', -18)
    .text(d => dimensions[d].name);

  // Add brushing
  dimensionGroups
    .append('g')
    .attr("class", "brush")
    .each(function(d) {
      var brush =
        d3.brushY()
          .extent([[-10, -2], [10, h + 2]]);

      var brushG = d3.select(this).call(brush);

      brush.on('brush', function(dim) {
        var brushExtent = d3.brushSelection(brushG.node());

        // Detect if any of our points in this dimension are within/without
        // the brush and update their data and rendering accordingly
        svg.selectAll("path.laptop").each(function(laptop) {
          var laptopYDimValue = dimensions[dim].yValueFunction(laptop);
          var laptopYDimPoint = dimensions[dim].yScale(laptopYDimValue);
          if(brushExtent[0] < laptopYDimPoint && laptopYDimPoint < brushExtent[1]) {
            laptop.brushes = laptop.brushes || {};
            laptop.brushes[dim] = true;
          } else {
            laptop.brushes = laptop.brushes || {};
            laptop.brushes[dim] = false;
          }
        });

        updateBrushes(svg, dimensions, colour, data, table);
      }).on('end', function(dim) {
        var brushExtent = d3.brushSelection(brushG.node());
        if(brushExtent === null) {
          data.forEach(laptop => {
            delete laptop.brushes[dim];
          });
        }

        updateBrushes(svg, dimensions, colour, data, table);
      });

      return brushG;
    })
    .selectAll("rect")
    .attr("x", -8)
    .attr("width", 16);
}

function updateBrushes(svg, dimensions, colour, data, table) {
  svg.selectAll("path.laptop").each(function(laptop) {
    // Update the 'inAllBrushes' if there are any brushes, indicating that this
    // laptop is within all brushes
    if(laptop.brushes) {
      laptop.inAllBrushes = Object.keys(dimensions).reduce((allTrue, dim) => {
        return allTrue && (laptop.brushes[dim] === undefined || laptop.brushes[dim]);
      }, true);
    } else {
      delete laptop.inAllBrushes;
    }

    // Change the colour of this line accordingly
    if(laptop.inAllBrushes === true || laptop.inAllBrushes === undefined) {
      d3.select(this).style('stroke', d => colour(d.price_aud));
    } else {
      var c = d3.rgb(106, 115, 125);
      c.opacity = 0.05;
      d3.select(this).style('stroke', c);
    }
  });

  renderTable(table, dimensions, data);
}

function createTable(data, dimensions) {
  var table =
    d3.select('#table')
      .append('table');

  var tableHeader = table.append('tr');

  // Create the non-dimensional table headers.
  tableHeader.append('th').text('Name');

  // Create the dimensional table headers.
  Object.keys(dimensions).map(dim => {
    tableHeader
      .append('th')
      .text(dimensions[dim].name);
  });

  tableHeader.append('th').text('Link');

  return table;
}

function renderTable(table, dimensions, data) {
  // Create our rows from the active data
  var activeData = data.filter(laptop => {
    return laptop.inAllBrushes === true || laptop.inAllBrushes === undefined;
  });

  activeData.sort((a, b) => d3.ascending(a.name, b.name));

  var onEnter = enter => {
    enter
      .append('tr')
      .attr('class', 'laptop')
      .each(function(laptop) {
        var row = d3.select(this);

        // Extra non-dimensional fields
        row.append('td').text(laptop.name);

        // Dimensional fields
        Object.keys(dimensions).map(dim => {
          var value = dimensions[dim].yValueFunction(laptop);

          if(dimensions[dim].tickFormat) {
            value = dimensions[dim].tickFormat(value);
          }

          row.append('td').text(value);
        });

        // Extra non-dimensional fields
        row
          .append('td')
          .append('a')
          .attr('href', laptop.url)
          .attr('class', 'table-link')
          .text('Details (external)');

      });
  };

  // We call data with `laptop.url` as the index as we can't rely on the position
  // in the array since we sort it. If we don't use an index it causes weird issues
  // where laptop names are duplicated in the table depending on the order they are
  // added/removed and their relative sort order
  table
    .selectAll('tr.laptop')
    .data(activeData, laptop => laptop.url)
    .join(onEnter);
}

function loadLaptopChart(dimensions) {
  d3.json('./data/laptops.json')
    .then(cleanData)
    .then(data => {
      var chartData = createChart(data);
      var svg = chartData[0];
      var w = chartData[1];
      var h = chartData[2];

      var table = createTable(data, dimensions);

      renderLaptopChart(svg, w, h, dimensions, data, table);
      renderTable(table, dimensions, data);
    })
    .catch(function(err) { console.log("Error loading data: " + err); });
}


function init() {
  loadLaptopChart(getDimensions());
}

function getDimensions() {
  return {
    price_aud: {
      name: "Price (AUD)",
      yValueFunction: (laptop) => +laptop.price_aud,
      tickFormat: d3.format("($.0f"),
      scaleType: 'linear'
    },
    cpu: {
      name: "CPU",
      sortFunction: (a, b) => d3.ascending(a.cpu, b.cpu),
      yValueFunction: (laptop) => laptop.cpu,
      scaleType: 'point'
    },
    ram_gbs: {
      name: "RAM (gb)",
      yValueFunction: (laptop) => +laptop.ram_gbs,
      sortFunction: (a, b) => d3.ascending(+a.ram_gbs, +b.ram_gbs),
      scaleType: 'point'
    },
    storage: {
      name: "Disk Space",
      yValueFunction: (laptop) => laptop.storage_text,
      sortFunction: (a, b) => d3.ascending(a.storage_value, b.storage_value),
      scaleType: 'point'
    },
    graphics_card: {
      name: "Graphics Card",
      yValueFunction: (laptop) => laptop.graphics_card.name,
      scaleType: 'point',
      sortFunction: (a, b) => {
        return d3.ascending(a.graphics_card.model_power, b.graphics_card.model_power) ||
          d3.ascending(a.graphics_card.model_number, a.graphics_card.model_number) ||
          d3.ascending(a.graphics_card.memory_gbs || 0 , b.graphics_card.memory_gbs || 0);
      }
    },
    weight_kgs: {
      name: "Weight (kg)",
      yValueFunction: (laptop) => +laptop.weight_kgs,
      scaleType: 'linear'
    },
    screen_size_inches: {
      name: "Screen Size (inches)",
      yValueFunction: (laptop) => +laptop.screen_size_inches,
      scaleType: 'linear'
    },
    brand: {
      name: "Brand",
      yValueFunction: (laptop) => laptop.brand,
      scaleType: 'point',
      sortFunction: (a, b) => d3.descending(a.brand, b.brand)
    }
  };
}

window.onload = init;
