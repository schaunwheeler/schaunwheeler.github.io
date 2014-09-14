
    (function(global) {
        window._datatables_onload_callbacks = [];

        datatablesjs_url = "http://cdn.datatables.net/1.10.2/js/jquery.dataTables.min.js"
        scripts = document.getElementsByTagName('script')
        for (i = 0; i < scripts.length; ++i) {
            if (scripts[i].src == datatablesjs_url) {
                scripts[i].parentNode.removeChild(scripts[i])
            }
        }

        function load_lib(url, callback){
            window._datatables_onload_callbacks.push(callback);
            console.log("data tables.js not loaded, scheduling load and callback at", new Date());
            window._datatables_is_loading = true;
            var s = document.createElement('script');
            s.src = url;
            s.async = true;
            s.onreadystatechange = s.onload = function(){
               window._datatables_onload_callbacks.forEach(function(callback){callback()});
            };
            s.onerror = function(){
                console.warn("failed to load library " + url);
            };
            document.getElementsByTagName("head")[0].appendChild(s);
        }

        var elt = document.getElementById("dataframe_table");
        if(elt==null) {
            console.log("ERROR: DataTable autoload script configured with elementid 'dataframe_table' but no matching script tag was found. ")
            return false;
        }

        var table_data = [{"Last Name":"Aldrich","First Name":"Dia","Performance":"0.02","Cluster Average":"0.95","Index":"-0.93"},{"Last Name":"Hickman","First Name":"Danyelle","Performance":"0.15","Cluster Average":"0.99","Index":"-0.84"},{"Last Name":"Valerio","First Name":"Song","Performance":"0.05","Cluster Average":"0.87","Index":"-0.82"},{"Last Name":"Chow","First Name":"Kami","Performance":"0.04","Cluster Average":"0.82","Index":"-0.78"},{"Last Name":"Geary","First Name":"Carleen","Performance":"0.13","Cluster Average":"0.84","Index":"-0.71"},{"Last Name":"Quick","First Name":"Paulene","Performance":"0.24","Cluster Average":"0.90","Index":"-0.66"},{"Last Name":"Rounds","First Name":"Adrianna","Performance":"0.35","Cluster Average":"0.99","Index":"-0.64"},{"Last Name":"Elrod","First Name":"Myrtie","Performance":"0.13","Cluster Average":"0.75","Index":"-0.61"},{"Last Name":"Riggs","First Name":"Rey","Performance":"0.27","Cluster Average":"0.88","Index":"-0.61"},{"Last Name":"Lund","First Name":"Aimee","Performance":"0.22","Cluster Average":"0.83","Index":"-0.61"},{"Last Name":"Lai","First Name":"Delphia","Performance":"0.19","Cluster Average":"0.76","Index":"-0.56"},{"Last Name":"Blocker","First Name":"Nickole","Performance":"0.25","Cluster Average":"0.80","Index":"-0.55"},{"Last Name":"Whitney","First Name":"Carlyn","Performance":"0.14","Cluster Average":"0.69","Index":"-0.55"},{"Last Name":"Kohn","First Name":"Trinidad","Performance":"0.41","Cluster Average":"0.95","Index":"-0.54"},{"Last Name":"Dudley","First Name":"Neida","Performance":"0.31","Cluster Average":"0.81","Index":"-0.50"},{"Last Name":"Duvall","First Name":"Rosy","Performance":"0.23","Cluster Average":"0.72","Index":"-0.49"},{"Last Name":"Fuentes","First Name":"Aida","Performance":"0.20","Cluster Average":"0.67","Index":"-0.47"},{"Last Name":"Minton","First Name":"Christa","Performance":"0.25","Cluster Average":"0.72","Index":"-0.47"},{"Last Name":"Hinson","First Name":"Lavone","Performance":"0.26","Cluster Average":"0.73","Index":"-0.47"},{"Last Name":"Cornish","First Name":"Jacquie","Performance":"0.34","Cluster Average":"0.81","Index":"-0.47"},{"Last Name":"Tanaka","First Name":"Mikel","Performance":"0.20","Cluster Average":"0.64","Index":"-0.45"},{"Last Name":"Purcell","First Name":"Valentine","Performance":"0.04","Cluster Average":"0.48","Index":"-0.44"},{"Last Name":"Collado","First Name":"Tammie","Performance":"0.39","Cluster Average":"0.82","Index":"-0.43"},{"Last Name":"Carnes","First Name":"Numbers","Performance":"0.11","Cluster Average":"0.54","Index":"-0.43"},{"Last Name":"Mackenzie","First Name":"Davina","Performance":"0.44","Cluster Average":"0.86","Index":"-0.43"},{"Last Name":"Branham","First Name":"Dong","Performance":"0.24","Cluster Average":"0.66","Index":"-0.42"},{"Last Name":"Rife","First Name":"Osvaldo","Performance":"0.50","Cluster Average":"0.93","Index":"-0.42"},{"Last Name":"Mosher","First Name":"Tilda","Performance":"0.53","Cluster Average":"0.95","Index":"-0.42"},{"Last Name":"Flaherty","First Name":"Jenifer","Performance":"0.46","Cluster Average":"0.86","Index":"-0.40"},{"Last Name":"Landis","First Name":"Karolyn","Performance":"0.32","Cluster Average":"0.73","Index":"-0.40"},{"Last Name":"Pointer","First Name":"Maisha","Performance":"0.52","Cluster Average":"0.91","Index":"-0.39"},{"Last Name":"Abernathy","First Name":"Modesta","Performance":"0.40","Cluster Average":"0.78","Index":"-0.39"},{"Last Name":"Cho","First Name":"Ayanna","Performance":"0.43","Cluster Average":"0.81","Index":"-0.38"},{"Last Name":"Tyson","First Name":"Yulanda","Performance":"0.46","Cluster Average":"0.82","Index":"-0.37"},{"Last Name":"Carey","First Name":"Aundrea","Performance":"0.35","Cluster Average":"0.70","Index":"-0.35"},{"Last Name":"Healy","First Name":"Terina","Performance":"0.11","Cluster Average":"0.46","Index":"-0.35"},{"Last Name":"Harlow","First Name":"Theda","Performance":"0.55","Cluster Average":"0.90","Index":"-0.34"},{"Last Name":"Kearns","First Name":"Olin","Performance":"0.48","Cluster Average":"0.82","Index":"-0.34"},{"Last Name":"Charles","First Name":"Jae","Performance":"0.07","Cluster Average":"0.41","Index":"-0.34"},{"Last Name":"Neill","First Name":"Cristin","Performance":"0.40","Cluster Average":"0.71","Index":"-0.31"},{"Last Name":"Schumacher","First Name":"Lesa","Performance":"0.58","Cluster Average":"0.86","Index":"-0.28"},{"Last Name":"Linares","First Name":"Ronni","Performance":"0.11","Cluster Average":"0.37","Index":"-0.26"},{"Last Name":"Nieves","First Name":"Mason","Performance":"0.66","Cluster Average":"0.91","Index":"-0.26"},{"Last Name":"Ludwig","First Name":"Shayna","Performance":"0.42","Cluster Average":"0.67","Index":"-0.25"},{"Last Name":"Proffitt","First Name":"Nicolle","Performance":"0.31","Cluster Average":"0.55","Index":"-0.24"},{"Last Name":"Flannery","First Name":"Cari","Performance":"0.38","Cluster Average":"0.62","Index":"-0.24"},{"Last Name":"Spicer","First Name":"Lorette","Performance":"0.41","Cluster Average":"0.64","Index":"-0.23"},{"Last Name":"Schroeder","First Name":"Belen","Performance":"0.37","Cluster Average":"0.59","Index":"-0.21"},{"Last Name":"Baughman","First Name":"Lilli","Performance":"0.77","Cluster Average":"0.98","Index":"-0.21"},{"Last Name":"Britt","First Name":"Millie","Performance":"0.60","Cluster Average":"0.79","Index":"-0.20"},{"Last Name":"Branch","First Name":"Rozanne","Performance":"0.68","Cluster Average":"0.87","Index":"-0.19"},{"Last Name":"Keck","First Name":"Demetrius","Performance":"0.50","Cluster Average":"0.68","Index":"-0.19"},{"Last Name":"Romeo","First Name":"Arletta","Performance":"0.44","Cluster Average":"0.62","Index":"-0.18"},{"Last Name":"Drury","First Name":"Carmella","Performance":"0.73","Cluster Average":"0.90","Index":"-0.17"},{"Last Name":"Upton","First Name":"Su","Performance":"0.29","Cluster Average":"0.45","Index":"-0.15"},{"Last Name":"Gleason","First Name":"Elvina","Performance":"0.73","Cluster Average":"0.89","Index":"-0.15"},{"Last Name":"Beckett","First Name":"Sherlene","Performance":"0.42","Cluster Average":"0.57","Index":"-0.15"},{"Last Name":"Mcdowell","First Name":"Floria","Performance":"0.32","Cluster Average":"0.42","Index":"-0.10"},{"Last Name":"Levine","First Name":"Lavona","Performance":"0.65","Cluster Average":"0.74","Index":"-0.10"},{"Last Name":"Bales","First Name":"Darcel","Performance":"0.88","Cluster Average":"0.97","Index":"-0.09"},{"Last Name":"Dye","First Name":"Tyree","Performance":"0.49","Cluster Average":"0.58","Index":"-0.09"},{"Last Name":"Ivey","First Name":"Peggie","Performance":"0.58","Cluster Average":"0.66","Index":"-0.08"},{"Last Name":"Chalmers","First Name":"Breanne","Performance":"0.45","Cluster Average":"0.52","Index":"-0.08"},{"Last Name":"Morse","First Name":"Sunday","Performance":"0.52","Cluster Average":"0.58","Index":"-0.06"},{"Last Name":"Avalos","First Name":"Londa","Performance":"0.66","Cluster Average":"0.71","Index":"-0.05"},{"Last Name":"Hobbs","First Name":"Tamisha","Performance":"0.78","Cluster Average":"0.81","Index":"-0.03"},{"Last Name":"Noe","First Name":"Takako","Performance":"0.63","Cluster Average":"0.64","Index":"-0.01"},{"Last Name":"Bartels","First Name":"Ivory","Performance":"0.59","Cluster Average":"0.55","Index":"0.03"},{"Last Name":"Luster","First Name":"Senaida","Performance":"0.62","Cluster Average":"0.58","Index":"0.04"},{"Last Name":"Bartley","First Name":"Zenaida","Performance":"0.23","Cluster Average":"0.16","Index":"0.07"},{"Last Name":"Bloom","First Name":"Sabina","Performance":"0.89","Cluster Average":"0.82","Index":"0.07"},{"Last Name":"Mcmullen","First Name":"Leif","Performance":"0.61","Cluster Average":"0.42","Index":"0.19"},{"Last Name":"Tovar","First Name":"Temika","Performance":"0.40","Cluster Average":"0.17","Index":"0.23"},{"Last Name":"Kruse","First Name":"Bobbye","Performance":"0.79","Cluster Average":"0.51","Index":"0.28"},{"Last Name":"Kenny","First Name":"Monika","Performance":"0.94","Cluster Average":"0.59","Index":"0.34"},{"Last Name":"Reichert","First Name":"Elliot","Performance":"0.75","Cluster Average":"0.36","Index":"0.39"},{"Last Name":"Marlowe","First Name":"Samuel","Performance":"0.82","Cluster Average":"0.34","Index":"0.47"},{"Last Name":"Rosser","First Name":"Carey","Performance":"0.95","Cluster Average":"0.44","Index":"0.51"}];
var table_columns = [{'mData': 'Last Name'}, {'mData': 'First Name'}, {'mData': 'Performance'}, {'mData': 'Cluster Average'}, {'mData': 'Index'}];


        function inject_table() {
            if (typeof $.fn.DataTable == "undefined") {
                $.fn.DataTable = jQuery.fn.DataTable;
            }
            if (typeof jQuery.fn.DataTable == "undefined") {
                jQuery.fn.DataTable = $.fn.DataTable;
            }
            var elem = $('.tableholder script#dataframe_table').get(0);
            var table_elem = document.createElement('table');
            table_elem.setAttribute("class", "display compact")
            var header = table_elem.createTHead();
            var tr = document.createElement('TR');
            header.appendChild(tr);
            for (i = 0; i < table_columns.length; i++) {
                var th = document.createElement('TH')
                th.appendChild(document.createTextNode(table_columns[i]['mData']));
                tr.appendChild(th);
            }
            var par = elem.parentElement
            par.insertBefore(table_elem, elem.nextSibling)

            // Setup - add a text input to each footer cell
            $(table_elem).find('thead th').each(function () {
                var title = $(table_elem).find('thead th').eq($(this).index()).text();
                $(this).html('<input type="text" placeholder= "' + title + '" />');
            });

            $(table_elem).DataTable({
                "bDestroy": true,
                "aaData": table_data,
                "aoColumns": table_columns,
                "iDisplayLength": 15,
                "aLengthMenu": [
                    [5, 15, 25, 50],
                    [5, 15, 25, 50]
                ]
            });

            // Apply the search
            $(table_elem).DataTable().columns().eq(0).each(function (colIdx) {
                $('input', $(table_elem).DataTable().column(colIdx).header()).on('keyup change', function () {
                    $(table_elem).DataTable()
                        .column(colIdx)
                        .search(this.value)
                        .draw();
                });
            });
        }

        function wait(name, callback) {
                var interval = 10; // ms
                window.setTimeout(function() {
                    if ($(name).length>0) {
                        callback();
                    } else {
                        window.setTimeout(arguments.callee, interval);
                    }
                }, interval);
            }


        load_lib(datatablesjs_url, function() {
            console.log("DataTable autoload callback at", new Date())
            wait(".tableholder script#dataframe_table", function(){
                console.log("Injecting DataTable with id 'dataframe_table'")
                    inject_table()
            });
        });
    }(this));
    