(function(global) {
  if (typeof (window._bokeh_onload_callbacks) === "undefined"){
    window._bokeh_onload_callbacks = [];
  }
  function load_lib(url, callback){
    window._bokeh_onload_callbacks.push(callback);
    if (window._bokeh_is_loading){
      console.log("BokehJS is being loaded, scheduling callback at", new Date());
      return null;
    }
    console.log("BokehJS not loaded, scheduling load and callback at", new Date());
    window._bokeh_is_loading = true;
    var s = document.createElement('script');
    s.src = url;
    s.async = true;
    s.onreadystatechange = s.onload = function(){
      Bokeh.embed.inject_css("http://cdn.pydata.org/bokeh-0.5.1.min.css");
      window._bokeh_onload_callbacks.forEach(function(callback){callback()});
    };
    s.onerror = function(){
      console.warn("failed to load library " + url);
    };
    document.getElementsByTagName("head")[0].appendChild(s);
  }

  bokehjs_url = "http://cdn.pydata.org/bokeh-0.5.1.min.js"

  var elt = document.getElementById("p1_1_em_estimates_preds_test_2014");
  if(elt==null) {
    console.log("ERROR: Bokeh autoload.js configured with elementid 'p1_1_em_estimates_preds_test_2014' but no matching script tag was found. ")
    return false;
  }

  // These will be set for the static case

  if(typeof(Bokeh) !== "undefined") {
    console.log("BokehJS loaded, going straight to plotting");
    Bokeh.embed.inject_plot("p1_1_em_estimates_preds_test_2014", all_models);
  } else {
    load_lib(bokehjs_url, function() {
      console.log("BokehJS plotting callback run at", new Date())
      Bokeh.embed.inject_plot("p1_1_em_estimates_preds_test_2014", all_models);
    });
  }

}(this));