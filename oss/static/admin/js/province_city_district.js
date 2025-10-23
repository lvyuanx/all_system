function initProvinceCityDistrict(widgetEl, province, city, district) {
    const provinceSelect = widgetEl.querySelector('.province-select');
    const citySelect = widgetEl.querySelector('.city-select');
    const districtSelect = widgetEl.querySelector('.district-select');

    // TODO: 用你的数据源初始化省市区
    const data = {
        "北京": {"北京城区": ["东城", "西城"]},
        "上海": {"上海城区": ["黄浦", "徐汇"]},
    };

    // 填充省
    provinceSelect.innerHTML = '<option value="">请选择省</option>';
    Object.keys(data).forEach(p => {
        const opt = document.createElement('option');
        opt.value = p; opt.text = p;
        if(p === province) opt.selected = true;
        provinceSelect.appendChild(opt);
    });

    function fillCity() {
        const cities = data[provinceSelect.value] || {};
        citySelect.innerHTML = '<option value="">请选择市</option>';
        Object.keys(cities).forEach(c => {
            const opt = document.createElement('option');
            opt.value = c; opt.text = c;
            if(c === city) opt.selected = true;
            citySelect.appendChild(opt);
        });
        fillDistrict();
    }

    function fillDistrict() {
        const districts = data[provinceSelect.value]?.[citySelect.value] || [];
        districtSelect.innerHTML = '<option value="">请选择区</option>';
        districts.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d; opt.text = d;
            if(d === district) opt.selected = true;
            districtSelect.appendChild(opt);
        });
    }

    provinceSelect.addEventListener('change', fillCity);
    citySelect.addEventListener('change', fillDistrict);

    // 初始化
    fillCity();
}
