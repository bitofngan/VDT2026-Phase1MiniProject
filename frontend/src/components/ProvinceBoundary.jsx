import { useEffect } from "react";
import { useMap } from "@vis.gl/react-google-maps";

function normalizeProvinceName(text) {
  return String(text || "")
    .trim()
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[-–—_.]/g, " ")
    .replace(/\s+/g, " ");
}

const OLD_TO_NEW_PROVINCE = {
  "ha noi": "Hà Nội",
  "hue": "Huế",
  "thua thien hue": "Huế",
  "ha giang": "Tuyên Quang",
  "tuyen quang": "Tuyên Quang",
  "lao cai": "Lào Cai",
  "yen bai": "Lào Cai",
  "thai nguyen": "Thái Nguyên",
  "bac kan": "Thái Nguyên",
  "phu tho": "Phú Thọ",
  "vinh phuc": "Phú Thọ",
  "hoa binh": "Phú Thọ",
  "bac ninh": "Bắc Ninh",
  "bac giang": "Bắc Ninh",
  "hung yen": "Hưng Yên",
  "thai binh": "Hưng Yên",
  "hai phong": "Hải Phòng",
  "hai duong": "Hải Phòng",
  "ninh binh": "Ninh Bình",
  "nam dinh": "Ninh Bình",
  "ha nam": "Ninh Bình",
  "quang tri": "Quảng Trị",
  "quang binh": "Quảng Trị",
  "da nang": "Đà Nẵng",
  "quang nam": "Đà Nẵng",
  "quang ngai": "Quảng Ngãi",
  "kon tum": "Quảng Ngãi",
  "gia lai": "Gia Lai",
  "binh dinh": "Gia Lai",
  "khanh hoa": "Khánh Hòa",
  "ninh thuan": "Khánh Hòa",
  "lam dong": "Lâm Đồng",
  "dak nong": "Lâm Đồng",
  "binh thuan": "Lâm Đồng",
  "dak lak": "Đắk Lắk",
  "phu yen": "Đắk Lắk",
  "ho chi minh city": "TPHCM",
  "ho chi minh": "TPHCM",
  "thanh pho ho chi minh": "TPHCM",
  "tp ho chi minh": "TPHCM",
  "hcmc": "TPHCM",
  "binh duong": "TPHCM",
  "ba ria vung tau": "TPHCM",
  "con dao": "TPHCM",
  "dong nai": "Đồng Nai",
  "binh phuoc": "Đồng Nai",
  "tay ninh": "Tây Ninh",
  "long an": "Tây Ninh",
  "can tho": "Cần Thơ",
  "soc trang": "Cần Thơ",
  "hau giang": "Cần Thơ",
  "vinh long": "Vĩnh Long",
  "ben tre": "Vĩnh Long",
  "tra vinh": "Vĩnh Long",
  "dong thap": "Đồng Tháp",
  "tien giang": "Đồng Tháp",
  "ca mau": "Cà Mau",
  "bac lieu": "Cà Mau",
  "an giang": "An Giang",
  "kien giang": "An Giang",
};

function getOldProvinceName(feature) {
  return (
    feature.getProperty("shapeName") ||
    feature.getProperty("NAME_1") ||
    feature.getProperty("name") ||
    feature.getProperty("Name") ||
    feature.getProperty("province") ||
    feature.getProperty("Province")
  );
}

export default function ProvinceBoundary({ province }) {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    map.data.forEach((feature) => {
      map.data.remove(feature);
    });

    if (province === "ALL") return;

    map.data.loadGeoJson("/data/vietnam_adm1.geojson", null, () => {
      map.data.setStyle((feature) => {
        const oldProvince = getOldProvinceName(feature);
        const oldKey = normalizeProvinceName(oldProvince);
        const mappedProvince = OLD_TO_NEW_PROVINCE[oldKey] || oldProvince;

        const isSelected =
          normalizeProvinceName(mappedProvince) === normalizeProvinceName(province);

        return {
          visible: isSelected,
          strokeWeight: 4,
          strokeColor: "#1976d2",
          fillColor: "#1976d2",
          fillOpacity: 0.15,
        };
      });
    });
  }, [map, province]);

  return null;
}