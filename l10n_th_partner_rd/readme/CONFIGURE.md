Go to *Settings \> Technical \> Parameters \> RD Field Mapping* (debug
mode) to choose which contact field receives which RD data. Each line
writes its *Template* to its *Partner Field*, replacing the placeholders
by the RD data. The form of a line lists the placeholders below.

Placeholders formatted like a Thai address (empty when the RD has no
value):

- `{name}`: `vBranchTitleName vBranchName vSurname`, e.g. บริษัท อีโคซอฟต์ จำกัด
- `{house_no}`: `vHouseNumber`, e.g. 459/132
- `{building}`: อาคาร `vBuildingName`, e.g. อาคาร ไอที
- `{room}`: ห้อง `vRoomNumber`, e.g. ห้อง 301
- `{floor}`: ชั้น `vFloorNumber`, e.g. ชั้น 3
- `{village}`: หมู่บ้าน `vVillageName`, e.g. หมู่บ้าน โครงการ นิว ไฮบ์ สุขสวัสดิ์
- `{moo}`: หมู่ที่ `vMooNumber`, e.g. หมู่ที่ 5
- `{soi}`: ซอย `vSoiName`, e.g. ซอย 1
- `{yaek}`: แยก `vYaek`, e.g. แยก 2
- `{road}`: ถนน`vStreetName`, e.g. ถนนสุขสวัสดิ์
- `{sub_district}`: ต.`vThambol`, แขวง`vThambol` in Bangkok, e.g. แขวงราษฎร์บูรณะ
- `{district}`: อ.`vAmphur`, เขต`vAmphur` in Bangkok, e.g. เขตราษฎร์บูรณะ
- `{province}`: `vProvince`, e.g. กรุงเทพมหานคร
- `{zip}`: `vPostCode`, e.g. 10140

Raw keys of the RD service, as `{vNID}` etc. The RD sends `-` for an
empty value, which is replaced by nothing:

- `vNID`: Tax ID (13 digits), e.g. 0105554048641
- `vtin`: Former 10-digit Tax ID, usually empty
- `vtitleName`: Title of the taxpayer, e.g. บริษัท
- `vName`: Name of the taxpayer, e.g. อีโคซอฟต์ จำกัด
- `vSurname`: Surname, for a person
- `vBranchTitleName`: Title of the branch, e.g. บริษัท
- `vBranchName`: Name of the branch, e.g. อีโคซอฟต์ จำกัด
- `vBranchNumber`: Branch number, 0 for the head office, e.g. 0
- `vBuildingName`: Building
- `vRoomNumber`: Room number
- `vFloorNumber`: Floor
- `vVillageName`: Village, e.g. โครงการ นิว ไฮบ์ สุขสวัสดิ์
- `vHouseNumber`: House number, e.g. 459/132
- `vMooNumber`: Moo
- `vSoiName`: Soi
- `vYaek`: Yaek
- `vStreetName`: Road, e.g. สุขสวัสดิ์
- `vThambol`: Sub-district, e.g. ราษฎร์บูรณะ
- `vAmphur`: District, e.g. ราษฎร์บูรณะ
- `vProvince`: Province, e.g. กรุงเทพมหานคร
- `vPostCode`: Postal code, e.g. 10140
- `vBusinessFirstDate`: Business start date, Buddhist Era, e.g. 2554-11-07

Keys added later by the RD can be used the same way. Unknown
placeholders are replaced by nothing. For a relational field (e.g.
State), the result is searched by name among the Thai records. By
default the sub-district and the district have their own field, the
rest of the address goes to the street:

- Name: `{name}`
- Street:
  `{house_no} {building} {room} {floor} {village} {moo} {soi} {yaek} {road}`
- Street 2: `{sub_district}`
- City: `{district}`
- State: `{province}`
- Zip: `{zip}`

The address form of the Odoo localization (l10n_th) uses another
layout instead: Street `{building} {room} {floor} {village}`, Street 2
`{house_no} {moo} {soi} {yaek} {road}`, City `{sub_district} {district}`.

The URL of the RD service is stored in the system parameter
`l10n_th_partner_rd.vat_service_url`.
