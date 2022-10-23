if (window.File && window.FileReader && window.FileList && window.Blob) {
} else {
  alert('Ваш браузер не поддерживает работу с локальными файлами, ' +
    'установите, например, последний google-chrome или firefox')
  throw new Error("browser doesn't support File Api")
}

const REG_ROW_RE = /^(\d{2}-\d{2}-\d{4};\d{2}-\d{2}-\d{2};)|(=\d+;(\d+,\d+;){2})/
const REG_NAME_V0 = /(\d+)_+(\d+)_+(\d+)_+(\d+)/
const REG_NAME_V1 = /(\d+)_+(\d+)_+(\d+)/

const REG_CODES_DICT = {
  '8704': { city: 'tih', service: 'ctv', jur: null},
  '25552': { city: 'tih', service: 'internet', jur: true},
  '25551': { city: 'tih', service: 'internet', jur: false},
  '16605': { city: 'kor', service: 'ctv', jur: null},
  '29569': { city: 'kor', service: 'internet', jur: true},
  '29570': { city: 'kor', service: 'internet', jur: false},
}

const STATUS_MSG = {
  'AccountNotFound': {msg: 'л/с не найден', class: 'error'},
  'PaymentAlreadyExists': {msg: 'уже есть', class: 'info'},
  'PaymentCommandError': {msg: 'ошибка биллинга', class: 'error'},
  'PaymentNotFound': {msg: 'не внесён', class: 'error'},
  'CashboxError': {msg: 'ошибка кассы', class: 'error'}
}

const CITIES_DICT = {
  tih: 'Тихорецк',
  kor: 'Кореновск',
  // test: 'тест'
}
const SERVICES_DICT = {ctv: 'КТВ', internet: 'Интернет'}

const PLACES = {tih: 'Тихорецк, касса ТелеТайм', kor: 'Кореновск, касса ТелеТайм'}
const API_CONF = {timeout: 5 * 60 * 1000}

Vue.config.devtools = true
Vue.use(VueLoading)


window.app = new Vue({
  delimiters:['${', '}'],
  el: '#app',
  data: {
    service_options: SERVICES_DICT,
    city_options: CITIES_DICT,
    place_options: PLACES,
    file: null,
    currentTask: {
      active: false,
      cancelable: false,
      cancelled: false,
      variant: 'primary',
      caption: '-',
      pbMax: 100,
      pbVal: 0
    },
    total_row: '',
    table_params: {
      busy: false,
      pagination: {
        per_page: 5,
        page_options: [ 5, 10, 15 ],
        current_page: 1
      },
      fields: [
        {
          key: 'checked',
          label: '',
        },{
          key: 'datetime',
          label: 'дата/время',
          sortable: true,
          formatter: (value, key, item) => {
            return moment(value).format('DD.MM.YYYY HH:mm:ss')
          }
        },{
          key: 'operation_id',
          label: 'код операции',
          sortable: true
        },{
          key: 'account_id',
          label: 'л/счёт',
          sortable: true
        },{
          key: 'fullname',
          label: 'ФИО',
          sortable: true
        },{
          key: 'address',
          label: 'адрес',
          sortable: true
        },{
          key: 'sum_transferred',
          label: 'сумма',
          sortable: true
        },{
          key: 'billing',
          label: 'биллинг',
          sortable: true,
          tdClass: 'result_cell'
        },{
          key: 'fiscal',
          label: 'чек',
          sortable: true,
          tdClass: 'result_cell'
        },
      ]
    },
    reg: null,
    rpcReqId: 0,
  },
  computed: {
    checkedOnly () {
      return this.reg.records.filter((itm) => {
        return itm.checked
      })
    },
    checkedTotal () {
      let sumAccepted = 0.0
      let sumTransfered = 0.0
      this.checkedOnly.forEach((record) => {
        sumAccepted += parseFloat(record.sum_accepted)
        sumTransfered += parseFloat(record.sum_transferred)
      })
      return {
        amount: this.checkedOnly.length,
        accepted: Math.round(sumAccepted * 100) / 100,
        transferred: Math.round(sumTransfered * 100) / 100
      }
    },
    checkedAll: {
      get () {
        return !!this.reg.records.length &&
        this.checkedTotal.amount === this.reg.records.length
      },
      set (checked) {
        this.reg.records.forEach((itm) => {
          itm.checked = checked
        })
      }
    },
    checkedNone () {
      return this.checkedTotal.amount === 0
    },
    cityName () {
      return CITIES_DICT[this.reg.city]
    },
    placeName () {
      return PLACES[this.reg.place]
    }
  },
  created () {
    this.resetData()
  },
  methods: {
    checkboxChanged (index, value) {
      let cellEl = this.$refs.table.$el.querySelector('tbody>tr:nth-child(' + (index+1) + ')')
      if (cellEl !== null) {
        !!value ? cellEl.classList.remove('unchecked') : cellEl.classList.add('unchecked')
      }
    },
    checkboxClick (item) {
      if (this.currentTask.active) return
      item.checked = !item.checked
    },
    invertSelection () {
      this.reg.records.forEach((itm) => {
        itm.checked = !itm.checked
      })
    },
    fileInputChanged (e) {
      if (!e.target.files[0]) {
        return
      }

      return this.readFile(e.target.files[0])
    },
    resetData () {
      this.file = null
      this.total_row = ''
      this.reg = {
        city: null,
        place: 'tih',
        number: null,
        service: null,
        records: [],
        comment: null
      }
    },
    readFile (fobj) {
      this.resetData()
      if (fobj.size > 2**20) {
        alert('выбранный файл размером ' + (fobj.size / 2**20).toFixed(0) +
          ' Мбайт, должен быть не больше 2 Мбайт')
        return
      }
      let reader = new FileReader()
      reader.onload = (pe) => {
        if (pe.target.result.includes('Р”')) {
          reader.readAsText(fobj, opt_encoding='utf8')
        }

        let re_groups

        // somthing like '29569_2321014898_40702810030120101383_653.txt'
        //                srv      inn            rs            nreg
        if ((re_groups = REG_NAME_V0.exec(fobj.name)) !== null) {
            let service_obj = REG_CODES_DICT[re_groups[1]]
            if (service_obj) {
              this.reg.service = service_obj.service
              this.reg.city = service_obj.city
              this.reg.place = service_obj.city || 'tih'
            }
            this.reg.number = re_groups[4]

        // somthing like '25552_04072018_0149.txt'
        //                srv     date   nreg
        } else if ((re_groups = REG_NAME_V1.exec(fobj.name)) !== null) {
            let service_obj = REG_CODES_DICT[re_groups[1]]
            if (service_obj) {
              this.reg.service = service_obj.service
              this.reg.city = service_obj.city
              this.reg.place = service_obj.city || 'tih'
            }
            this.reg.number = re_groups[3]
        }

        this.parseFile(pe.target.result)
      }

      reader.readAsText(fobj, opt_encoding='cp1251')
    },
    parseFile (text) {
      this.reg.records = []
      let line_sep = '\n'

      text.replace(/\r/g, line_sep).replace(/\n\n/g, line_sep)
      text.split(line_sep).forEach((row) => {
        if (!REG_ROW_RE.test(row.trim())) {
          return
        }
        let it_is_total_row = row.startsWith('=')
        let fields = (it_is_total_row ? row.slice(1) : row).split(';')

        if (it_is_total_row) {
          this.total_row = row
        }
        else {
          // //      0          1     2    3        4            5   6
          // // 27-06-2018;09-20-04;8619;8619999V;800055093337;639;СТРЕКАЛОВ АЛЕКСАНДР АЛЕКСАНДРОВИЧ;
          // //     7                                8  9    10     11     12
          // // Г.КОРЕНОВСК УЛ.МЕДВЕДЕВА Д.24 КВ.81;  ;   ;800,00;800,00;0,00;
          record = {
            datetime: moment(fields[0] + ' ' + fields[1], 'DD-MM-YYYY HH-mm-ss').toDate().getTime(),
            office_number: parseInt(fields[2]),
            cashier_id: fields[3],
            operation_id: fields[4],
            account_id: fields[5],
            fullname: fields[6],
            address: fields[7]
          }

          // operation_id from the bank is not unique enough
          record.operation_id += record.datetime

          switch (fields.length - 1) {
            case 11:
              record = {...record, ...{
                info: null,
                sum_accepted: parseFloat(fields[8].replace(/,/g, '.')),
                sum_transferred: parseFloat(fields[9].replace(/,/g, '.')),
                bank_commission: parseFloat(fields[10].replace(/,/g, '.'))
              }}
              break;

            case 12:
              record = {...record, ...{
                info: fields[8],
                sum_accepted: parseFloat(fields[9].replace(/,/g, '.')),
                sum_transferred: parseFloat(fields[10].replace(/,/g, '.')),
                bank_commission: parseFloat(fields[11].replace(/,/g, '.'))
              }}
              break;

            case 13:
              record = {...record, ...{
                info: fields[8] + ' ' + fields[9],
                sum_accepted: parseFloat(fields[10].replace(/,/g, '.')),
                sum_transferred: parseFloat(fields[11].replace(/,/g, '.')),
                bank_commission: parseFloat(fields[12].replace(/,/g, '.'))
              }}
              break;
          }
          record['checked'] = true
          record['billing'] = {msg: null, class: 'normal'},
          record['fiscal'] = {msg: null, class: 'normal'}

          this.reg.records.push(record)
        }
      })
    },

    reqOne (idx, method) {
      let record = this.checkedOnly[idx]
      let params
      let field

      switch (method) {

        case 'make_fiscal':
          params = {
            service_code: this.reg.service,
            order_id: record.operation_id,
            paysum: record.sum_transferred,
            place: this.placeName
          }
          field = 'fiscal'
          break

        case 'make_payment':
          params = {
            city_code: this.reg.city,
            pay_ext_id: record.operation_id,
            pay_timestamp: parseInt(record.datetime) > 0 ? record.datetime / 1000 : null,
            paysum: record.sum_transferred,
            account_id: record.account_id,
            comment: this.reg.comment
          }
          field = 'billing'
          break

        default:
          return
      }

      axios.post('/api', {jsonrpc: "2.0", id: ++this.rpcReqId, method: method, params: params}, API_CONF)

      .then((resp) => {
          if (resp.data.hasOwnProperty('error') && resp.data.error !== null) {
            let errorMd = STATUS_MSG[resp.data.error.data.type]
            if (typeof errorMd === 'undefined') {
              record[field] = {msg: 'ошибка API', class: 'error'}
            } else {
              record[field] = errorMd
            }
          } else {
            record[field] = {msg: method === 'make_fiscal' ? resp.data.result : 'ok', class: 'success'}
          }
        })

      .catch((err) => {
          console.error(err)
          record[field] = {msg: 'ошибка', class: 'error'}
        })

      .finally(() => {
          this.currentTask.pbVal++
          if (idx + 1 === this.checkedTotal.amount) {
            setTimeout(()=>{this.currentTask.active = false}, 1000)
            return
          }

          if (this.currentTask.cancelled) {
            this.checkedOnly.forEach((record) => {
              if (record[field].class === 'normal loading') {
                record[field] = {msg: '', class: 'normal'}
              }
            })
            this.currentTask.active = false
            this.currentTask.cancelled = false
            return
          }

          this.reqOne(idx + 1, method)
        })
    },

    startReqChain (method) {
      if (this.checkedTotal.amount < 1) {return}
      let field
      let caption
      let variant

      switch (method) {

        case 'make_fiscal':
          caption = 'формирование чеков (' + SERVICES_DICT[this.reg.service] + ', ' + CITIES_DICT[this.reg.city] + ')'
          variant = 'primary'
          field = 'fiscal'
          break

        case 'make_payment':
          caption = 'разнос платежей (Интернет, ' + CITIES_DICT[this.reg.city] + ')'
          variant = 'success'
          field = 'billing'
          break

        default:
          return
      }

      this.currentTask = {
        active: true,
        cancelable: true,
        cancelled: false,
        caption: caption,
        variant: variant,
        pbVal: 0,
        pbMax: this.checkedTotal.amount,
      }

      this.checkedOnly.forEach((record) => {
        record[field] = {msg: '', class: 'normal loading'}
      })

      this.reqOne(0, method)
    }
  }
})
