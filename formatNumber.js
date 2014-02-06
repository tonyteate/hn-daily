//http://stackoverflow.com/questions/2692323/code-golf-friendly-number-abbreviator
function m(n,d){
  p=Math.pow;
  d=p(10,d);
  i=7;
  while(i)(s=p(10,i--*3))<=n&&(n=Math.round(n*d/s)/d+"kMBTPE"[i]);
  return n
}

//http://stackoverflow.com/questions/2685911/is-there-a-way-to-round-numbers-into-a-reader-friendly-format-e-g-1-1k
function abbrNum(number, decPlaces) {
    // 2 decimal places => 100, 3 => 1000, etc
    decPlaces = Math.pow(10,decPlaces);

    // Enumerate number abbreviations
    var abbrev = [ "k", "m", "b", "t" ];

    // Go through the array backwards, so we do the largest first
    for (var i=abbrev.length-1; i>=0; i--) {

        // Convert array index to "1000", "1000000", etc
        var size = Math.pow(10,(i+1)*3);

        // If the number is bigger or equal do the abbreviation
        if(size <= number) {
             // Here, we multiply by decPlaces, round, and then divide by decPlaces.
             // This gives us nice rounding to a particular decimal place.
             number = Math.round(number*decPlaces/size)/decPlaces;

             // Handle special case where we round up to the next abbreviation
             if((number == 1000) && (i < abbrev.length - 1)) {
                 number = 1;
                 i++;
             }

             // Add the letter for the abbreviation
             number += abbrev[i];

             // We are done... stop
             break;
        }
    }

    return number;
}


//https://github.com/HubSpot/humanize/blob/master/public/src/humanize.js
normalizePrecision = function(value, base) {
    value = Math.round(Math.abs(value));
    if (isNaN(value)) {
      return base;
    } else {
      return value;
    }
  };

toFixed = function(value, precision) {
    var power;
    if (precision == null) {
      precision = normalizePrecision(precision, 0);
    }
    power = Math.pow(10, precision);
    return (Math.round(value * power) / power).toFixed(precision);
  };


formatNumber = function(number, precision, thousand, decimal) {
    var base, commas, decimals, firstComma, mod, negative, usePrecision,
      _this = this;
    if (precision == null) {
      precision = 0;
    }
    if (thousand == null) {
      thousand = ",";
    }
    if (decimal == null) {
      decimal = ".";
    }
    firstComma = function(number, thousand, position) {
      if (position) {
        return number.substr(0, position) + thousand;
      } else {
        return "";
      }
    };
    commas = function(number, thousand, position) {
      return number.substr(position).replace(/(\d{3})(?=\d)/g, "$1" + thousand);
    };
    decimals = function(number, decimal, usePrecision) {
      if (usePrecision) {
        return decimal + toFixed(Math.abs(number), usePrecision).split(".")[1];
      } else {
        return "";
      }
    };
    usePrecision = normalizePrecision(precision);
    negative = number < 0 && "-" || "";
    base = parseInt(toFixed(Math.abs(number || 0), usePrecision), 10) + "";
    mod = base.length > 3 ? base.length % 3 : 0;
    return negative + firstComma(base, thousand, mod) + commas(base, thousand, mod) + decimals(number, decimal, usePrecision);
  };