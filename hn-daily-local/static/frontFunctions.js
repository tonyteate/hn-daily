//http://stackoverflow.com/questions/2692323/code-golf-friendly-number-abbreviator
function n2shjs(n,d){
  p=Math.pow;
  d=p(10,d);
  i=7;
  while(i)(s=p(10,i--*3))<=n&&(n=Math.round(n*d/s)/d+"kMBTPE"[i]);
  return n
}