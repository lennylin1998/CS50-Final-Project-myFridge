$(document).ready(function(){
  // Create an extendable form on the grocery page
  $('.purchase').val(new Date().toISOString().slice(0, 10));
    let count = 1;
  $('#item-block').on('click', '.btn.btn-danger', function(event){
    event.preventDefault();
    event.stopPropagation();
    $(this).parent().parent().remove();
  });
  $("#btn-plus").click(function(event){
    event.preventDefault();
    // Set input values to default
    let item = $("#item-row").clone(true);
    $(item).find('input').each(function(){
        if ($(this).attr('class') != 'form-control purchase'){
          $(this).val('');
        }
    });
    // Change the button to minus button
    $("#item-row td:first").remove();
    $("#item-row").prepend('<td><button class="btn btn-danger" id="btn-minus"><i class="fa-solid fa-minus"></i></button></td>');
    $("#item-row").attr('id', 'item-old');
    $("#item-block").append(item);
    $("#item-row input").each(function(){
    $(this).attr('name', this.getAttribute("name").slice(0, 3) + "-" + "" + count);
    });
    $("#item-row select").each(function(){
    $(this).attr('name', this.getAttribute("name").slice(0, 3) + "-" + "" + count);
    });
    count ++;
  });
  // Include Datatable to display items on fridge page
  $('#datatable').DataTable({
    columnDefs:
    [
      {
        searchPanes: {
          show: true,
          viewCount: false,
          orderable: false,
          initCollapsed: true
        },
        targets: [2, 3]
      },
      {orderable: false, targets: [0, 1, 2]},
    ],
    dom: 'Plfrtip',
    order:[4, 'asc'],
    paging: false,
    info: false
  });
  // Add input field to the item on fridge page when the item is checked
  $(".form-check-input").click(function(){
    let quantity = $(this).parent().parent().find("div");
    let href = $('#create-recipe-link').attr('href');
    if ($(this).prop("checked"))
    {
      let quantity_text = quantity.text();
      let number = quantity_text.match(/\d/g);
      let numbers = number.join("");
      let letter = quantity_text.match(/\D+/g);
      let unit = letter.join("");
      quantity.text('');
      quantity.append(`<input type="number" class="form-control" name="qtn-${$(this).attr('id')}" placeholder="${numbers}" value="${numbers}"> ${unit}`);
      if (href.indexOf('?') >= 0){
        href = href + `&id=${$(this).attr('id')}`;
      }
      else {
        href = href + `?id=${$(this).attr('id')}`;
      }
    }
    else if (!$(this).prop('checked'))
    {
      original_text = quantity.find('input').attr('placeholder');
      quantity.find('input').remove();
      quantity.prepend(original_text);
      let position = href.indexOf(`id=${$(this).attr('id')}`);
      if (href[position - 1] == '?'){
        href = href.replace(`?id=${$(this).attr('id')}`, '');
        href = href.replace(href[href.indexOf('&')], '?');
      }
      else {
        href = href.replace(`&id=${$(this).attr('id')}`, '');
      }
    }
    $('#create-recipe-link').attr('href', href);
  });
  // Create modal that pops up when submit form on fridge page
  $("input[type=checkbox]").change(function(){
    if ($("#datatable input[type=checkbox]:checked").length == 0){
      $("#cook-btn, #recipe-btn").prop("disabled", true);
    }
    else{
      $("#cook-btn, #recipe-btn").prop("disabled", false);
    };
  });
  // Edit hyper link when check items
  $("input[type=checkbox]").change()
  // Create DataTable on recipe page
  $('#recipe-table').DataTable({
    columnDefs:[
      {visible: false, targets: [2]}
    ],
    paging: false,
    order:[1, 'desc'],
    info: false
  });
  $('#ingredient-table').DataTable({
    columnDefs:[
      {orderable: false, targets: [0, 1, 2]}
    ],
    searching: false,
    paging: false,
    info: false
  });
  //Add row-selecttion script for selecting recipes
  $('#recipe-table').on('draw.dt', function(){
    let first_result = $(this).find('tbody tr').first();
    if ($(first_result).find('td').attr("class") == "dataTables_empty"){
      $('#ajax-body').find('tr').remove();
      $('#ajax-body').html('<tr class="odd"><td valign="top" colspan="3" class="dataTables_empty">No data available in table</td></tr>');
      $("input[name='recipe-cook-btn']").prop("disabled", true);
    }
    else{
      $("input[name='recipe-cook-btn']").prop("disabled", false);
    }
    $(first_result).trigger('click');
  });
  $('#recipe-table tbody tr').click(function(){
    $(this).attr('class', 'selected').siblings().removeClass('selected');
    $(this).trigger('classChange');
    let id_selected = $(this).find('td').first().attr("id")
    $("#recipe-id").val(id_selected);
    $('#edit-link').attr('href', `recipe/edit?id=${id_selected}`)
  });
  $('#recipe-table').on('classChange', function(){
    let recipe_id = $(this).find('.selected td').first().attr("id");
    let ajax_body = $("#ajax-body");
    // Store default null row data from datatable
    $(ajax_body).find("tr").remove();
    $.ajax("/ingredients", {
      data: {id: recipe_id}
    }).done(function(data){
      // Append ingredients data to table
      let shortage = false;
      for (let i = 0; i < data.length; i++){
        $(ajax_body).append(`<tr class="${data[i].cookable}"> <td>${data[i].item}</td> <td>${data[i].category}</td> <td>${data[i].quantity} ${data[i].unit}</td> </tr>`);
        if (data[i].cookable == "shortage"){
          shortage = true;
        }
      }
      // If any of the ingredient is in shortage, disable the cook button
      if (shortage == true){
        $("input[name='recipe-cook-btn']").prop("disabled", true);
      }
      else {
        $("input[name='recipe-cook-btn']").prop("disabled", false);
      }
    });
  });
});